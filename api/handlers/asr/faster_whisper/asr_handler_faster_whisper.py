import re
import os
import time
import torch
import numpy as np
import tempfile
from typing import Dict, Optional, cast
from loguru import logger
from pydantic import BaseModel, Field
from abc import ABC

from chat_engine.contexts.handler_context import HandlerContext
from chat_engine.data_models.chat_engine_config_data import ChatEngineConfigModel, HandlerBaseConfigModel
from chat_engine.common.handler_base import HandlerBase, HandlerBaseInfo, HandlerDataInfo, HandlerDetail
from chat_engine.data_models.chat_data.chat_data_model import ChatData
from chat_engine.data_models.chat_data_type import ChatDataType
from chat_engine.data_models.runtime_data.data_bundle import DataBundle, DataBundleDefinition, DataBundleEntry
from chat_engine.contexts.session_context import SessionContext

from engine_utils.directory_info import DirectoryInfo
from engine_utils.general_slicer import SliceContext, slice_data

# Import Faster-Whisper
from faster_whisper import WhisperModel


class ASRConfig(HandlerBaseConfigModel, BaseModel):
    model_size: str = Field(default="large-v3")  # Options: tiny, base, small, medium, large-v1, large-v2, large-v3
    language: str = Field(default="pl")  # Polish language by default
    device: str = Field(default="auto")  # auto, cpu, cuda
    compute_type: str = Field(default="float16")  # float16, int8, int8_float16
    
    # Accuracy-focused settings
    beam_size: int = Field(default=5)  # Higher for better accuracy
    best_of: int = Field(default=5)  # Higher for better accuracy
    patience: float = Field(default=2.0)  # Higher for better accuracy
    length_penalty: float = Field(default=1.0)
    repetition_penalty: float = Field(default=1.0)
    no_repeat_ngram_size: int = Field(default=0)
    temperature: float = Field(default=0.0)  # Lower for more consistent results
    
    # Audio processing settings
    sample_rate: int = Field(default=16000)
    channels: int = Field(default=1)
    chunk_size: int = Field(default=1024)
    
    # Additional precision optimizations
    audio_device: str = Field(default="respeaker_stt")
    vad_threshold: float = Field(default=0.4)
    energy_threshold: int = Field(default=200)
    dynamic_energy_threshold: bool = Field(default=True)
    dynamic_energy_adjustment_damping: float = Field(default=0.1)
    dynamic_energy_ratio: float = Field(default=2.0)
    pause_threshold: float = Field(default=1.2)
    phrase_threshold: float = Field(default=0.2)
    non_speaking_duration: float = Field(default=0.3)


class ASRContext(HandlerContext):
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.config = None
        self.local_session_id = 0
        self.output_audios = []
        self.audio_slice_context = SliceContext.create_numpy_slice_context(
            slice_size=16000,
            slice_axis=0,
        )
        self.cache = {}

        self.dump_audio = True
        self.audio_dump_file = None
        if self.dump_audio:
            dump_file_path = os.path.join(DirectoryInfo.get_project_dir(),
                                          "dump_talk_audio_faster_whisper.pcm")
            self.audio_dump_file = open(dump_file_path, "wb")
        self.shared_states = None


class HandlerASR(HandlerBase, ABC):
    def __init__(self):
        super().__init__()
        self.model_size = 'large-v3'
        self.language = 'pl'
        self.device = 'auto'
        self.compute_type = 'float16'
        self.model = None
        
        # Accuracy settings
        self.beam_size = 5
        self.best_of = 5
        self.patience = 2.0
        self.length_penalty = 1.0
        self.repetition_penalty = 1.0
        self.no_repeat_ngram_size = 0
        self.temperature = 0.0
        
        # Audio processing settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # Precision optimizations
        self.audio_device = "respeaker_stt"
        self.vad_threshold = 0.4
        self.energy_threshold = 200
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.1
        self.dynamic_energy_ratio = 2.0
        self.pause_threshold = 1.2
        self.phrase_threshold = 0.2
        self.non_speaking_duration = 0.3

        # Auto-detect device
        if torch.cuda.is_available():
            self.device_fallback = "cuda"
        else:
            self.device_fallback = "cpu"

    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(
            name="ASR_Faster_Whisper",
            config_model=ASRConfig,
        )

    def get_handler_detail(self, session_context: SessionContext,
                           context: HandlerContext) -> HandlerDetail:
        definition = DataBundleDefinition()
        definition.add_entry(DataBundleEntry.create_audio_entry("avatar_audio", 1, 24000))
        inputs = {
            ChatDataType.HUMAN_AUDIO: HandlerDataInfo(
                type=ChatDataType.HUMAN_AUDIO,
            )
        }
        outputs = {
            ChatDataType.HUMAN_TEXT: HandlerDataInfo(
                type=ChatDataType.HUMAN_TEXT,
                definition=definition,
            )
        }
        return HandlerDetail(
            inputs=inputs, outputs=outputs,
        )

    def load(self, engine_config: ChatEngineConfigModel, handler_config: Optional[BaseModel] = None):
        if isinstance(handler_config, ASRConfig):
            self.model_size = handler_config.model_size
            self.language = handler_config.language
            self.device = handler_config.device if handler_config.device != "auto" else self.device_fallback
            self.compute_type = handler_config.compute_type
            
            # Accuracy settings
            self.beam_size = handler_config.beam_size
            self.best_of = handler_config.best_of
            self.patience = handler_config.patience
            self.length_penalty = handler_config.length_penalty
            self.repetition_penalty = handler_config.repetition_penalty
            self.no_repeat_ngram_size = handler_config.no_repeat_ngram_size
            self.temperature = handler_config.temperature
            
            # Audio settings
            self.sample_rate = handler_config.sample_rate
            self.channels = handler_config.channels
            self.chunk_size = handler_config.chunk_size
            
            # Precision settings
            self.audio_device = handler_config.audio_device
            self.vad_threshold = handler_config.vad_threshold
            self.energy_threshold = handler_config.energy_threshold
            self.dynamic_energy_threshold = handler_config.dynamic_energy_threshold
            self.dynamic_energy_adjustment_damping = handler_config.dynamic_energy_adjustment_damping
            self.dynamic_energy_ratio = handler_config.dynamic_energy_ratio
            self.pause_threshold = handler_config.pause_threshold
            self.phrase_threshold = handler_config.phrase_threshold
            self.non_speaking_duration = handler_config.non_speaking_duration

        logger.info(f"Loading Faster-Whisper model: {self.model_size} for language: {self.language}")
        logger.info(f"Device: {self.device}, Compute type: {self.compute_type}")
        logger.info(f"Accuracy settings - Beam size: {self.beam_size}, Best of: {self.best_of}, Temperature: {self.temperature}")
        
        self.model = WhisperModel(
            self.model_size, 
            device=self.device, 
            compute_type=self.compute_type,
            download_root="models/faster-whisper"  # Store models in your models directory
        )
        logger.info("Faster-Whisper model loaded successfully")

    def create_context(self, session_context, handler_config=None):
        if not isinstance(handler_config, ASRConfig):
            handler_config = ASRConfig()
        context = ASRContext(session_context.session_info.session_id)
        context.shared_states = session_context.shared_states
        return context
    
    def start_context(self, session_context, handler_context):
        pass

    def handle(self, context: HandlerContext, inputs: ChatData,
               output_definitions: Dict[ChatDataType, HandlerDataInfo]):

        output_definition = output_definitions.get(ChatDataType.HUMAN_TEXT).definition
        context = cast(ASRContext, context)
        if inputs.type == ChatDataType.HUMAN_AUDIO:
            audio = inputs.data.get_main_data()
        else:
            return
        speech_id = inputs.data.get_meta("speech_id")
        if (speech_id is None):
            speech_id = context.session_id

        if audio is not None:
            audio = audio.squeeze()
            logger.info('Audio input received')
            for audio_segment in slice_data(context.audio_slice_context, audio):
                if audio_segment is None or audio_segment.shape[0] == 0:
                    continue
                context.output_audios.append(audio_segment)

        speech_end = inputs.data.get_meta("human_speech_end", False)
        if not speech_end:
            return

        # Prefill remainder audio in slice context
        remainder_audio = context.audio_slice_context.flush()
        if remainder_audio is not None:
            if remainder_audio.shape[0] < context.audio_slice_context.slice_size:
                remainder_audio = np.concatenate(
                    [remainder_audio,
                     np.zeros(shape=(context.audio_slice_context.slice_size - remainder_audio.shape[0]))])
                context.output_audios.append(remainder_audio)
        
        if not context.output_audios:
            return
            
        output_audio = np.concatenate(context.output_audios)
        if context.audio_dump_file is not None:
            logger.info('Dumping audio to file')
            context.audio_dump_file.write(output_audio.tobytes())

        # Convert audio to float32 and normalize
        audio_float = output_audio.astype(np.float32)
        if audio_float.dtype == np.int16:
            audio_float = audio_float / 32768.0
        
        # Transcribe with Faster-Whisper
        try:
            logger.info(f"Transcribing audio with Faster-Whisper (language: {self.language})")
            start_time = time.time()
            
            # Use high-accuracy settings
            segments, info = self.model.transcribe(
                audio_float,
                language=self.language,
                beam_size=self.beam_size,
                best_of=self.best_of,
                patience=self.patience,
                length_penalty=self.length_penalty,
                repetition_penalty=self.repetition_penalty,
                no_repeat_ngram_size=self.no_repeat_ngram_size,
                temperature=self.temperature,
                compression_ratio_threshold=2.4,  # Filter out poor quality
                log_prob_threshold=-1.0,  # Filter out low confidence
                no_speech_threshold=0.6,  # Filter out non-speech
                condition_on_previous_text=True,  # Use context
                prompt_reset_on_temperature=0.5,  # Reset prompt on high temp
                initial_prompt=None,
                prefix=None,
                suppress_blank=True,
                suppress_tokens=[-1],
                without_timestamps=False,
                max_initial_timestamp=0.0,
                word_timestamps=False
            )
            
            transcribe_time = time.time() - start_time
            
            # Combine all segments
            output_text = ""
            segment_count = 0
            for segment in segments:
                output_text += segment.text
                segment_count += 1
            
            output_text = output_text.strip()
            
            logger.info(f"Faster-Whisper transcription completed in {transcribe_time:.2f}s")
            logger.info(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
            logger.info(f"Processed {segment_count} segments")
            logger.info(f"Transcription result: {output_text}")
            
        except Exception as e:
            logger.error(f"Error during Faster-Whisper transcription: {e}")
            output_text = ""

        context.output_audios.clear()

        if len(output_text) == 0:
            # If transcription result is empty, re-enable VAD
            context.shared_states.enable_vad = True
            return

        output = DataBundle(output_definition)
        output.set_main_data(output_text)
        output.add_meta('human_text_end', False)
        output.add_meta('speech_id', speech_id)
        yield output

        end_output = DataBundle(output_definition)
        end_output.set_main_data('')
        end_output.add_meta("human_text_end", True)
        end_output.add_meta("speech_id", speech_id)
        yield end_output

    def destroy_context(self, context: HandlerContext):
        context = cast(ASRContext, context)
        if context.audio_dump_file is not None:
            context.audio_dump_file.close()
        pass
