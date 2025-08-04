import io
import os
import re
import time
import subprocess
import tempfile
from typing import Dict, Optional, cast
import librosa
import numpy as np
from loguru import logger
from pydantic import BaseModel, Field
from abc import ABC
from chat_engine.contexts.handler_context import HandlerContext
from chat_engine.data_models.chat_engine_config_data import ChatEngineConfigModel, HandlerBaseConfigModel
from chat_engine.common.handler_base import HandlerBase, HandlerBaseInfo, HandlerDataInfo, HandlerDetail
from chat_engine.data_models.chat_data.chat_data_model import ChatData
from chat_engine.data_models.chat_data_type import ChatDataType
from chat_engine.contexts.session_context import SessionContext
from chat_engine.data_models.runtime_data.data_bundle import DataBundle, DataBundleDefinition, DataBundleEntry
from engine_utils.directory_info import DirectoryInfo


class PiperTTSConfig(HandlerBaseConfigModel, BaseModel):
    model_path: str = Field(default="models/piper/pl_PL-mls_6892-medium.onnx")
    config_path: str = Field(default="models/piper/pl_PL-mls_6892-medium.onnx.json")
    sample_rate: int = Field(default=22050)
    speaker_id: Optional[int] = Field(default=None)
    length_scale: float = Field(default=1.0)  # Speed control (1.0 = normal, < 1.0 = faster, > 1.0 = slower)
    noise_scale: float = Field(default=0.667)  # Voice variation
    noise_w: float = Field(default=0.8)  # Phoneme variation


class PiperTTSContext(HandlerContext):
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.config = None
        self.local_session_id = 0
        self.input_text = ''
        self.dump_audio = False
        self.audio_dump_file = None
        self.piper_process = None  # Keep persistent Piper process


class HandlerPiperTTS(HandlerBase, ABC):
    def __init__(self):
        super().__init__()
        self.model_path = None
        self.config_path = None
        self.sample_rate = None
        self.speaker_id = None
        self.length_scale = None
        self.noise_scale = None
        self.noise_w = None
        self.piper_executable = None
        self._find_piper_executable()

    def _find_piper_executable(self):
        """Find piper executable in system PATH or common locations"""
        # Try to find piper in PATH first
        try:
            result = subprocess.run(['which', 'piper'], capture_output=True, text=True)
            if result.returncode == 0:
                self.piper_executable = result.stdout.strip()
                logger.info(f"Found piper executable: {self.piper_executable}")
                return
        except:
            pass
        
        # Try common installation paths
        common_paths = [
            '/usr/local/bin/piper',
            '/usr/bin/piper',
            '/opt/piper/piper',
            os.path.expanduser('~/.local/bin/piper'),
            './piper',
        ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                self.piper_executable = path
                logger.info(f"Found piper executable: {self.piper_executable}")
                return
        
        logger.warning("Piper executable not found. Please install piper-tts or ensure it's in PATH")
        self.piper_executable = 'piper'  # Fallback, will likely fail

    def get_handler_info(self) -> HandlerBaseInfo:
        return HandlerBaseInfo(
            config_model=PiperTTSConfig,
        )

    def get_handler_detail(self, session_context: SessionContext,
                           context: HandlerContext) -> HandlerDetail:
        definition = DataBundleDefinition()
        definition.add_entry(DataBundleEntry.create_audio_entry("avatar_audio", 1, self.sample_rate))
        inputs = {
            ChatDataType.AVATAR_TEXT: HandlerDataInfo(
                type=ChatDataType.AVATAR_TEXT,
            )
        }
        outputs = {
            ChatDataType.AVATAR_AUDIO: HandlerDataInfo(
                type=ChatDataType.AVATAR_AUDIO,
                definition=definition,
            )
        }
        return HandlerDetail(
            inputs=inputs, outputs=outputs,
        )

    def load(self, engine_config: ChatEngineConfigModel, handler_config: Optional[BaseModel] = None):
        config = cast(PiperTTSConfig, handler_config)
        
        # Make paths absolute relative to project root
        project_root = DirectoryInfo.get_project_dir()
        if not os.path.isabs(config.model_path):
            self.model_path = os.path.join(project_root, config.model_path)
        else:
            self.model_path = config.model_path
            
        if not os.path.isabs(config.config_path):
            self.config_path = os.path.join(project_root, config.config_path)
        else:
            self.config_path = config.config_path
            
        self.sample_rate = config.sample_rate
        self.speaker_id = config.speaker_id
        self.length_scale = config.length_scale
        self.noise_scale = config.noise_scale
        self.noise_w = config.noise_w
        
        # Find piper executable
        self._find_piper_executable()
        
        # Verify model files exist
        if not os.path.exists(self.model_path):
            logger.error(f"Piper model file not found: {self.model_path}")
            raise FileNotFoundError(f"Piper model file not found: {self.model_path}")
        
        if not os.path.exists(self.config_path):
            logger.error(f"Piper config file not found: {self.config_path}")
            raise FileNotFoundError(f"Piper config file not found: {self.config_path}")
        
        logger.info(f"Loaded PiperTTS with model: {self.model_path}")

    def create_context(self, session_context, handler_config=None):
        if not isinstance(handler_config, PiperTTSConfig):
            handler_config = PiperTTSConfig()
        context = PiperTTSContext(session_context.session_info.session_id)
        context.input_text = ''
        if context.dump_audio:
            dump_file_path = os.path.join(DirectoryInfo.get_project_dir(), 'temp',
                                            f"dump_avatar_audio_{context.session_id}_{time.localtime().tm_hour}_{time.localtime().tm_min}.pcm")
            context.audio_dump_file = open(dump_file_path, "wb")
        return context
    
    def start_context(self, session_context, context: HandlerContext):
        context = cast(PiperTTSContext, context)
        # Start persistent Piper process for faster synthesis
        try:
            self._start_piper_process(context)
            # Test synthesis to warm up the model
            self._synthesize_text_fast(context, "Test")
            logger.info("PiperTTS context started successfully with persistent process")
        except Exception as e:
            logger.warning(f"PiperTTS persistent process failed, falling back to subprocess mode: {e}")
            
    def _start_piper_process(self, context: PiperTTSContext):
        """Start a persistent Piper process for faster synthesis"""
        cmd = [
            self.piper_executable,
            '--model', self.model_path,
            '--output_file', '-',  # Output to stdout
        ]
        
        # Add essential parameters
        if self.length_scale != 1.0:
            cmd.extend(['--length_scale', str(self.length_scale)])
        if self.noise_scale != 0.667:
            cmd.extend(['--noise_scale', str(self.noise_scale)])
        if self.noise_w != 0.8:
            cmd.extend(['--noise_w', str(self.noise_w)])
            
        logger.info(f"Starting persistent Piper process: {' '.join(cmd)}")
        context.piper_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # Use binary mode for better performance
            bufsize=0    # Unbuffered for immediate response
        )

    def filter_text(self, text):
        # Include Polish diacritics: ą, ć, ę, ł, ń, ó, ś, ź, ż (and their uppercase versions)
        pattern = r"[^a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ0-9\u4e00-\u9fff,.\~!?，。！？ \-:]"  # Allow Polish characters
        filtered_text = re.sub(pattern, "", text)
        return filtered_text

    def _synthesize_text_fast(self, context: PiperTTSContext, text: str) -> np.ndarray:
        """
        Optimized synthesis with reduced overhead
        """
        try:
            # Use /tmp for faster I/O and auto-cleanup
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True, dir='/tmp') as temp_file:
                temp_path = temp_file.name
            
            # Minimal command for maximum speed
            cmd = [
                self.piper_executable,
                '--model', self.model_path,
                '--output_file', temp_path
            ]
            
            # Only add changed parameters to minimize command length
            if self.length_scale != 1.0:
                cmd.extend(['--length_scale', str(self.length_scale)])
            if self.noise_scale != 0.667:
                cmd.extend(['--noise_scale', str(self.noise_scale)])
            if self.noise_w != 0.8:
                cmd.extend(['--noise_w', str(self.noise_w)])
            
            # Fast execution with minimal overhead
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                timeout=1.5,  # Very aggressive timeout
                env={'PYTHONUNBUFFERED': '1', 'OMP_NUM_THREADS': '1'},  # Single thread for speed
                cwd='/tmp'  # Use /tmp for faster file I/O
            )
            
            if result.returncode != 0:
                logger.warning(f"Piper synthesis failed for: {text[:30]}...")
                return np.zeros(shape=(24000,), dtype=np.float32)
            
            # Ultra-fast audio loading
            output_audio, _ = librosa.load(temp_path, sr=24000, mono=True)
            
            # Minimal normalization
            max_val = np.max(np.abs(output_audio))
            if max_val > 0:
                output_audio = output_audio * (0.7 / max_val)
            
            return output_audio.astype(np.float32)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Synthesis timeout (1.5s) for: {text[:30]}...")
            return np.zeros(shape=(24000,), dtype=np.float32)
        except Exception as e:
            logger.error(f"Fast synthesis error: {e}")
            return np.zeros(shape=(24000,), dtype=np.float32)

    def _synthesize_text(self, text: str) -> np.ndarray:
        """Synthesize text using Piper TTS"""
        try:
            # Create temporary file for output (faster file I/O approach)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Prepare Piper command with minimal parameters for speed
                cmd = [
                    self.piper_executable,
                    '--model', self.model_path,
                    '--output_file', temp_path,
                ]
                
                # Add essential parameters only
                if self.length_scale != 1.0:
                    cmd.extend(['--length_scale', str(self.length_scale)])
                if self.noise_scale != 0.667:
                    cmd.extend(['--noise_scale', str(self.noise_scale)])
                if self.noise_w != 0.8:
                    cmd.extend(['--noise_w', str(self.noise_w)])
                
                # Run Piper with optimized settings
                result = subprocess.run(
                    cmd,
                    input=text,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=3  # Shorter timeout for responsiveness
                )
                
                # Load audio directly with target sample rate for speed
                output_audio, original_sr = librosa.load(temp_path, sr=24000, mono=True)  # Load directly at 24kHz
                
                # Quick normalization
                max_amplitude = np.max(np.abs(output_audio))
                if max_amplitude > 0:
                    output_audio = output_audio * (0.7 / max_amplitude)
                
                # Return as 1D array
                return output_audio.astype(np.float32)
                
            finally:
                # Clean up temporary file quickly
                try:
                    os.unlink(temp_path)
                except:
                    pass  # Ignore cleanup errors for speed
            
        except subprocess.TimeoutExpired:
            logger.error(f"Piper synthesis timeout for text: {text[:50]}...")
            return np.zeros(shape=(24000,), dtype=np.float32)  # 1 second of silence at 24kHz
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper subprocess error: {e.stderr}")
            return np.zeros(shape=(24000,), dtype=np.float32)  # 1 second of silence at 24kHz
        except Exception as e:
            logger.error(f"Error in Piper synthesis: {e}")
            return np.zeros(shape=(24000,), dtype=np.float32)  # 1 second of silence at 24kHz

    def handle(self, context: HandlerContext, inputs: ChatData,
               output_definitions: Dict[ChatDataType, HandlerDataInfo]):
        output_definition = output_definitions.get(ChatDataType.AVATAR_AUDIO).definition
        context = cast(PiperTTSContext, context)
        
        if inputs.type == ChatDataType.AVATAR_TEXT:
            text = inputs.data.get_main_data()
        else:
            return
            
        speech_id = inputs.data.get_meta("speech_id")
        if speech_id is None:
            speech_id = context.session_id

        if text is not None:
            text = re.sub(r"<\|.*?\|>", "", text)
            context.input_text += self.filter_text(text)

        text_end = inputs.data.get_meta("avatar_text_end", False)
        if not text_end:
            sentences = re.split(r'(?<=[,.~!?，。！？])', context.input_text)
            if len(sentences) > 1:  # At least one complete sentence
                complete_sentences = sentences[:-1]  # Complete sentences
                context.input_text = sentences[-1]  # Remaining incomplete part

                # Process complete sentences
                for sentence in complete_sentences:
                    if len(sentence.strip()) < 1:
                        continue
                    logger.info('current sentence' + sentence)
                    
                    # Add timing to track synthesis speed
                    start_time = time.time()
                    output_audio = self._synthesize_text_fast(context, sentence)
                    synthesis_time = time.time() - start_time
                    logger.info(f"Synthesis took {synthesis_time:.2f}s for sentence: {sentence[:50]}...")
                    
                    output_audio = output_audio[np.newaxis, ...]
                    output = DataBundle(output_definition)
                    output.set_main_data(output_audio)
                    output.add_meta("avatar_speech_end", False)
                    output.add_meta("speech_id", speech_id)
                    context.submit_data(output)
        else:
            logger.info('last sentence' + context.input_text)
            if context.input_text is not None and len(context.input_text.strip()) > 0:
                start_time = time.time()
                output_audio = self._synthesize_text_fast(context, context.input_text)
                synthesis_time = time.time() - start_time
                logger.info(f"Final synthesis took {synthesis_time:.2f}s for: {context.input_text[:50]}...")
                
                output_audio = output_audio[np.newaxis, ...]
                output = DataBundle(output_definition)
                output.set_main_data(output_audio)
                output.add_meta("avatar_speech_end", False)
                output.add_meta("speech_id", speech_id)
                context.submit_data(output)
                
            context.input_text = ''
            output = DataBundle(output_definition)
            output.set_main_data(np.zeros(shape=(1, 24000), dtype=np.float32))  # 1 second of silence at 24kHz
            output.add_meta("avatar_speech_end", True)
            output.add_meta("speech_id", speech_id)
            context.submit_data(output)
            logger.info("speech end")

    def destroy_context(self, context: HandlerContext):
        context = cast(PiperTTSContext, context)
        # Clean up persistent process
        if context.piper_process:
            try:
                context.piper_process.terminate()
                context.piper_process.wait(timeout=1)
            except:
                try:
                    context.piper_process.kill()
                except:
                    pass
        logger.info('Destroy PiperTTS context')
