import io
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

# Import AssemblyAI
import assemblyai as aai
import wave


class ASRConfig(HandlerBaseConfigModel, BaseModel):
    api_key: str = Field(default="13f04fb3c4f9431890b60142a7862438")
    speech_model: str = Field(default="best")  # "best" or "nano"
    language: str = Field(default="pl")  # Polish language by default


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
                                          "dump_talk_audio_assemblyai.pcm")
            self.audio_dump_file = open(dump_file_path, "wb")
        self.shared_states = None


class HandlerASR(HandlerBase, ABC):
    def __init__(self):
        super().__init__()
        self.api_key = "13f04fb3c4f9431890b60142a7862438"
        self.speech_model = "best"
        self.language = "pl"
        self.transcriber = None

        # Device is not relevant for AssemblyAI as it's a cloud service
        self.device = "cloud"

    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(
            name="ASR_AssemblyAI",
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
            self.api_key = handler_config.api_key
            self.speech_model = handler_config.speech_model
            self.language = handler_config.language

        logger.info(f"Initializing AssemblyAI with speech model: {self.speech_model} for language: {self.language}")
        
        # Set API key
        aai.settings.api_key = self.api_key
        
        # Create transcription config
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best if self.speech_model == "best" else aai.SpeechModel.nano,
            language_code=self.language
        )
        
        # Create transcriber
        self.transcriber = aai.Transcriber(config=config)
        logger.info("AssemblyAI transcriber initialized successfully")

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

        # Convert audio to proper format for AssemblyAI
        # AssemblyAI expects 16-bit PCM audio
        if output_audio.dtype != np.int16:
            # Convert float audio to int16
            if output_audio.dtype == np.float32 or output_audio.dtype == np.float64:
                output_audio = (output_audio * 32767).astype(np.int16)
            else:
                output_audio = output_audio.astype(np.int16)
        
        # Transcribe with AssemblyAI
        try:
            logger.info(f"Transcribing audio with AssemblyAI (language: {self.language})")
            start_time = time.time()
            
            # Create a temporary WAV file for AssemblyAI
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Write WAV file
                with wave.open(temp_filename, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                    wav_file.setframerate(16000)  # 16kHz sample rate
                    wav_file.writeframes(output_audio.tobytes())
            
            # Transcribe using AssemblyAI
            transcript = self.transcriber.transcribe(temp_filename)
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            transcribe_time = time.time() - start_time
            logger.info(f"AssemblyAI transcription completed in {transcribe_time:.2f}s")
            
            if transcript.status == "error":
                logger.error(f"AssemblyAI transcription failed: {transcript.error}")
                output_text = ""
            else:
                output_text = transcript.text.strip() if transcript.text else ""
                logger.info(f"Transcription result: {output_text}")
            
        except Exception as e:
            logger.error(f"Error during AssemblyAI transcription: {e}")
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
