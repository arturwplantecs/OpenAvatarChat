import re
import os
import time
import torch
import numpy as np
from typing import Dict, Optional, cast
from loguru import logger
from pydantic import BaseModel, Field
from abc import ABC

# Set up CUDA environment for cuDNN compatibility
def setup_cuda_environment():
    """Setup comprehensive CUDA environment paths for cuDNN compatibility"""
    venv_path = os.environ.get('CONDA_PREFIX', '/opt/miniconda3/envs/py311')
    
    # Primary cuDNN path
    cudnn_lib_path = os.path.join(venv_path, 'lib', 'python3.11', 'site-packages', 'nvidia', 'cudnn', 'lib')
    
    # Additional CUDA library paths
    cuda_runtime_path = os.path.join(venv_path, 'nvidia', 'cuda_runtime', 'lib')
    cublas_path = os.path.join(venv_path, 'nvidia', 'cublas', 'lib')
    cufft_path = os.path.join(venv_path, 'nvidia', 'cufft', 'lib')
    curand_path = os.path.join(venv_path, 'nvidia', 'curand', 'lib')
    cusparse_path = os.path.join(venv_path, 'nvidia', 'cusparse', 'lib')
    
    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    new_paths = [cudnn_lib_path, cuda_runtime_path, cublas_path, cufft_path, curand_path, cusparse_path]
    
    for path in new_paths:
        if os.path.exists(path) and path not in current_ld_path:
            current_ld_path = f"{path}:{current_ld_path}" if current_ld_path else path
    
    os.environ['LD_LIBRARY_PATH'] = current_ld_path
    
    # Set specific cuDNN environment variables
    os.environ['CUDNN_INCLUDE_PATH'] = os.path.join(venv_path, 'nvidia', 'cudnn', 'include')
    os.environ['CUDNN_LIB_PATH'] = cudnn_lib_path
    
    # Suppress cuDNN version warnings and handle library loading
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    
    # Force disable problematic cuDNN operations that cause crashes
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    logger.info(f"Updated comprehensive CUDA environment for cuDNN compatibility")

# Setup CUDA environment before importing other modules
setup_cuda_environment()

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
    device: str = Field(default="auto")  # auto, cuda, cpu
    compute_type: str = Field(default="float16")  # int8, int16, float16, float32
    
    # Accuracy-focused settings
    beam_size: int = Field(default=5)  # Higher beam size for better accuracy
    best_of: int = Field(default=5)  # Number of candidates to consider
    patience: float = Field(default=1.0)  # Patience factor for beam search
    length_penalty: float = Field(default=1.0)  # Length penalty for beam search
    repetition_penalty: float = Field(default=1.0)  # Repetition penalty
    no_repeat_ngram_size: int = Field(default=0)  # Prevent repeating n-grams
    temperature: float = Field(default=0.0)  # Temperature for sampling (0.0 for deterministic)
    compression_ratio_threshold: float = Field(default=2.4)  # Compression ratio threshold
    log_prob_threshold: float = Field(default=-1.0)  # Log probability threshold
    no_speech_threshold: float = Field(default=0.6)  # No speech threshold
    
    # Audio processing settings
    sample_rate: int = Field(default=16000)
    channels: int = Field(default=1)
    chunk_size: int = Field(default=1024)
    
    # STT precision optimizations
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
        
        # Accuracy-focused settings
        self.beam_size = 5
        self.best_of = 5
        self.patience = 1.0
        self.length_penalty = 1.0
        self.repetition_penalty = 1.0
        self.no_repeat_ngram_size = 0
        self.temperature = 0.0
        self.compression_ratio_threshold = 2.4
        self.log_prob_threshold = -1.0
        self.no_speech_threshold = 0.6
        
        # Audio processing settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # STT precision optimizations
        self.audio_device = "respeaker_stt"
        self.vad_threshold = 0.4
        self.energy_threshold = 200
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.1
        self.dynamic_energy_ratio = 2.0
        self.pause_threshold = 1.2
        self.phrase_threshold = 0.2
        self.non_speaking_duration = 0.3

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
            self.device = handler_config.device
            self.compute_type = handler_config.compute_type
            
            # Accuracy-focused settings
            self.beam_size = handler_config.beam_size
            self.best_of = handler_config.best_of
            self.patience = handler_config.patience
            self.length_penalty = handler_config.length_penalty
            self.repetition_penalty = handler_config.repetition_penalty
            self.no_repeat_ngram_size = handler_config.no_repeat_ngram_size
            self.temperature = handler_config.temperature
            self.compression_ratio_threshold = handler_config.compression_ratio_threshold
            self.log_prob_threshold = handler_config.log_prob_threshold
            self.no_speech_threshold = handler_config.no_speech_threshold
            
            # Audio processing settings
            self.sample_rate = handler_config.sample_rate
            self.channels = handler_config.channels
            self.chunk_size = handler_config.chunk_size
            
            # STT precision optimizations
            self.audio_device = handler_config.audio_device
            self.vad_threshold = handler_config.vad_threshold
            self.energy_threshold = handler_config.energy_threshold
            self.dynamic_energy_threshold = handler_config.dynamic_energy_threshold
            self.dynamic_energy_adjustment_damping = handler_config.dynamic_energy_adjustment_damping
            self.dynamic_energy_ratio = handler_config.dynamic_energy_ratio
            self.pause_threshold = handler_config.pause_threshold
            self.phrase_threshold = handler_config.phrase_threshold
            self.non_speaking_duration = handler_config.non_speaking_duration

        # Determine device automatically if set to auto with cuDNN workaround
        if self.device == "auto":
            try:
                if torch.cuda.is_available():
                    # Test CUDA with a simple operation
                    test_tensor = torch.randn(1).cuda()
                    del test_tensor
                    
                    # Try to initialize a small Faster-Whisper model to test cuDNN
                    logger.info("Testing GPU compatibility with small model...")
                    try:
                        test_model = WhisperModel("tiny", device="cuda", compute_type="float16")
                        # Quick test transcription with empty audio
                        import numpy as np
                        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
                        list(test_model.transcribe(test_audio, beam_size=1))
                        del test_model
                        device = "cuda"
                        logger.info("GPU cuDNN test successful - using CUDA")
                    except Exception as cudnn_e:
                        if any(err in str(cudnn_e).lower() for err in ['cudnn', 'libcudnn', 'invalid handle']):
                            logger.warning(f"cuDNN issue detected: {cudnn_e}")
                            logger.info("Falling back to CPU due to cuDNN compatibility issues")
                            device = "cpu"
                        else:
                            raise cudnn_e
                else:
                    device = "cpu"
                    logger.info("CUDA not available, using CPU")
            except Exception as e:
                logger.warning(f"CUDA test failed: {e}")
                device = "cpu"
                logger.info("Falling back to CPU for Faster-Whisper")
        else:
            device = self.device

        # Adjust compute type based on device and avoid CUDA issues
        if device == "cpu" or device == "auto":
            # Always use int8 for CPU for better performance and compatibility
            compute_type = "int8"
            logger.info("Using int8 compute type for CPU")
        else:
            compute_type = self.compute_type
            logger.info(f"Using {compute_type} compute type for GPU")

        logger.info(f"Loading Faster-Whisper model: {self.model_size}")
        logger.info(f"Language: {self.language}, Device: {device}, Compute type: {compute_type}")
        logger.info(f"Accuracy settings - Beam size: {self.beam_size}, Best of: {self.best_of}, Temperature: {self.temperature}")
        
        # Load the model with accuracy-focused settings and error handling
        try:
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=4 if device == "cpu" else 0,
                num_workers=1
            )
            logger.info("Faster-Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model with {device}/{compute_type}, trying CPU/int8: {e}")
            # Fallback to CPU with int8
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                num_workers=1
            )
            logger.info("Faster-Whisper model loaded successfully on CPU fallback")

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
        
        # Transcribe with Faster-Whisper using accuracy-focused settings with GPU fallback
        try:
            logger.info(f"Transcribing audio with Faster-Whisper (language: {self.language})")
            start_time = time.time()
            
            # Suppress CUDA/cuDNN warnings during transcription by redirecting stderr
            import warnings
            import sys
            import contextlib
            from io import StringIO
            
            @contextlib.contextmanager
            def suppress_cuda_warnings():
                # Capture stderr to suppress cuDNN error messages
                old_stderr = sys.stderr
                sys.stderr = StringIO()
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', message='Unable to load any of')
                        warnings.filterwarnings('ignore', message='Invalid handle')
                        warnings.filterwarnings('ignore', category=UserWarning)
                        yield
                finally:
                    sys.stderr = old_stderr
                    
            with suppress_cuda_warnings():
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
                    compression_ratio_threshold=self.compression_ratio_threshold,
                    log_prob_threshold=self.log_prob_threshold,
                    no_speech_threshold=self.no_speech_threshold,
                    condition_on_previous_text=True,  # Use context for better accuracy
                    word_timestamps=False,  # Disable for faster processing
                    vad_filter=False,  # We handle VAD separately
                    vad_parameters=None
                )
            
            transcribe_time = time.time() - start_time
            logger.info(f"Faster-Whisper transcription completed in {transcribe_time:.2f}s")
            logger.info(f"Detected language: {info.language}, Probability: {info.language_probability:.2f}")
            
            # Combine all segments into text
            output_text = ""
            for segment in segments:
                output_text += segment.text
            
            output_text = output_text.strip()
            logger.info(f"Transcription result: {output_text}")
            
        except Exception as e:
            # Check if this is a CUDA/cuDNN error during transcription
            error_str = str(e).lower()
            if any(cuda_err in error_str for cuda_err in ['cudnn', 'cuda', 'gpu', 'libcudnn']):
                logger.warning(f"GPU transcription failed with CUDA/cuDNN error, falling back to CPU: {e}")
                try:
                    # Reload model on CPU for future transcriptions
                    logger.info("Reloading Faster-Whisper model on CPU for reliability")
                    self.model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=4,
                        num_workers=1
                    )
                    
                    # Retry transcription on CPU
                    logger.info("Retrying transcription on CPU")
                    start_time = time.time()
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
                        compression_ratio_threshold=self.compression_ratio_threshold,
                        log_prob_threshold=self.log_prob_threshold,
                        no_speech_threshold=self.no_speech_threshold,
                        condition_on_previous_text=True,
                        word_timestamps=False,
                        vad_filter=False,
                        vad_parameters=None
                    )
                    
                    transcribe_time = time.time() - start_time
                    logger.info(f"CPU transcription completed in {transcribe_time:.2f}s")
                    logger.info(f"Detected language: {info.language}, Probability: {info.language_probability:.2f}")
                    
                    # Combine all segments into text
                    output_text = ""
                    for segment in segments:
                        output_text += segment.text
                    
                    output_text = output_text.strip()
                    logger.info(f"Transcription result: {output_text}")
                    
                except Exception as cpu_e:
                    logger.error(f"CPU fallback transcription also failed: {cpu_e}")
                    output_text = ""
            else:
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
