import re
import os
import time
import torch
import numpy as np
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

# Import OpenAI Whisper
import whisper


class ASRConfig(HandlerBaseConfigModel, BaseModel):
    model_name: str = Field(default="base")
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
                                          "dump_talk_audio_whisper.pcm")
            self.audio_dump_file = open(dump_file_path, "wb")
        self.shared_states = None


class HandlerASR(HandlerBase, ABC):
    def __init__(self):
        super().__init__()
        self.model_name = 'base'
        self.language = 'pl'
        self.model = None

        if torch.cuda.is_available():
            self.device = torch.device("cuda:0")
        elif torch.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(
            name="ASR_OpenAI_Whisper",
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
            self.model_name = handler_config.model_name
            self.language = handler_config.language

        logger.info(f"Loading OpenAI Whisper model: {self.model_name} for language: {self.language}")
        self.model = whisper.load_model(self.model_name, device=self.device)
        logger.info("OpenAI Whisper model loaded successfully")

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
        
        # Transcribe with Whisper
        try:
            logger.info(f"Transcribing audio with Whisper (language: {self.language})")
            start_time = time.time()
            
            result = self.model.transcribe(
                audio_float, 
                language=self.language,
                task="transcribe",
                fp16=False,
                verbose=False
            )
            
            transcribe_time = time.time() - start_time
            logger.info(f"Whisper transcription completed in {transcribe_time:.2f}s")
            
            output_text = result["text"].strip()
            logger.info(f"Transcription result: {output_text}")
            
        except Exception as e:
            logger.error(f"Error during Whisper transcription: {e}")
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
