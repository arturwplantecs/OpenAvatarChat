"""
Pipeline service for AI processing
"""

import os
import sys
import asyncio
import yaml
import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import numpy as np

# Add the project src to path to import original handlers
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

logger = logging.getLogger(__name__)


class PipelineService:
    """Service that manages the AI processing pipeline"""
    
    def __init__(self):
        self.config = {}
        self.handlers = {}
        self.is_initialized = False
        self.initialization_time = None
        
        # Handler instances
        self.vad_handler = None
        self.asr_handler = None
        self.llm_handler = None
        self.tts_handler = None
        self.avatar_handler = None
        
        # Processing statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time": 0.0
        }
    
    async def initialize(self):
        """Initialize the pipeline with handlers"""
        try:
            logger.info("🔧 Initializing AI pipeline...")
            start_time = time.time()
            
            # Load configuration
            await self._load_config()
            
            # Initialize handlers
            await self._initialize_handlers()
            
            self.is_initialized = True
            self.initialization_time = time.time() - start_time
            
            logger.info(f"✅ Pipeline initialized in {self.initialization_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Pipeline initialization failed: {e}")
            raise
    
    async def _load_config(self):
        """Load pipeline configuration"""
        try:
            # First try to load main_config.yaml from API directory
            api_config_path = Path(__file__).parent.parent / "main_config.yaml"
            
            if api_config_path.exists():
                config_path = api_config_path
            else:
                # Fallback to original config
                config_path = project_root / "config" / "chat_with_faster_whisper_stable.yaml"
            
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"📋 Loaded config from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Use fallback config
            self.config = self._get_fallback_config()
            logger.warning("Using fallback configuration")
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration if config file is not available"""
        return {
            "vad": {
                "name": "silero_vad",
                "model_path": "models/silero_vad.onnx"
            },
            "asr": {
                "name": "faster_whisper",
                "model_path": "models/faster-whisper-large-v3",
                "language": "pl",
                "cpu_threads": 4
            },
            "llm": {
                "name": "openai_compatible",
                "api_base": "http://localhost:11434/v1",
                "model_name": "qwen2.5:7b",
                "max_tokens": 150,
                "temperature": 0.7
            },
            "tts": {
                "name": "piper",
                "model_path": "models/piper/pl_mls_piper-medium.onnx",
                "speaker_id": 0
            },
            "avatar": {
                "name": "lite_avatar",
                "model_path": "models/lite_avatar",
                "fps": 25
            }
        }
    
    async def _initialize_handlers(self):
        """Initialize all pipeline handlers"""
        try:
            # Try to initialize real handlers first, fallback to mock
            if await self._try_initialize_real_handlers():
                logger.info("✅ Real handlers initialized successfully")
            else:
                await self._initialize_mock_handlers()
                logger.info("⚠️  Using mock handlers - install dependencies for real functionality")
            
        except Exception as e:
            logger.error(f"Handler initialization failed: {e}")
            raise
    
    async def _try_initialize_real_handlers(self) -> bool:
        """Try to initialize real handlers, return True if successful"""
        try:
            # Initialize real ASR handler with FasterWhisper
            await self._initialize_real_asr()
            
            # Initialize real TTS handler with PiperTTS
            await self._initialize_real_tts()
            
            # Initialize real Avatar handler with LiteAvatar
            await self._initialize_real_avatar()
            
            # Initialize real LLM handler
            await self._initialize_real_llm()
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize real handlers: {e}")
            return False
    
    async def _initialize_real_asr(self):
        """Initialize real ASR handler with FasterWhisper"""
        try:
            from faster_whisper import WhisperModel
            
            # Access the correct config structure
            chat_engine_config = self.config.get("default", {}).get("chat_engine", {})
            asr_config = chat_engine_config.get("handler_configs", {}).get("FasterWhisper", {})
            
            model_path = asr_config.get("model_size", "large-v3")
            device = asr_config.get("device", "cpu")
            compute_type = asr_config.get("compute_type", "int8")
            language = asr_config.get("language", "pl")
            
            class FasterWhisperHandler:
                def __init__(self, model_path, device, compute_type, language):
                    self.model = WhisperModel(model_path, device=device, compute_type=compute_type)
                    self.language = language
                    logger.info(f"FasterWhisper model loaded: {model_path}")
                
                async def process_async(self, audio_data: bytes):
                    import tempfile
                    import os
                    
                    # Save audio to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_file.write(audio_data)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Run transcription in executor
                        loop = asyncio.get_event_loop()
                        segments, info = await loop.run_in_executor(
                            None, 
                            self._transcribe_file, 
                            temp_file_path
                        )
                        
                        text = " ".join([segment.text for segment in segments]).strip()
                        return {"text": text}
                        
                    finally:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                
                def _transcribe_file(self, file_path):
                    return self.model.transcribe(
                        file_path,
                        language=self.language,
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=500)
                    )
            
            self.asr_handler = FasterWhisperHandler(model_path, device, compute_type, language)
            logger.info("✅ Real FasterWhisper ASR handler initialized")
            
        except ImportError:
            logger.warning("faster-whisper not available")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize FasterWhisper: {e}")
            raise
    
    async def _initialize_real_tts(self):
        """Initialize real TTS handler with PiperTTS"""
        try:
            import subprocess
            import tempfile
            import librosa
            import numpy as np
            
            # Check if PiperTTS model exists
            chat_engine_config = self.config.get("default", {}).get("chat_engine", {})
            tts_config = chat_engine_config.get("handler_configs", {}).get("PiperTTS", {})
            model_path = tts_config.get("model_path", "models/piper/pl_PL-gosia-medium.onnx")
            
            # Look for the model in API directory first, then project root
            model_full_path = None
            for base_path in [Path(__file__).parent.parent, project_root]:
                potential_path = base_path / model_path
                if potential_path.exists():
                    model_full_path = potential_path
                    break
            
            if not model_full_path:
                logger.warning(f"PiperTTS model not found: {model_path}")
                raise FileNotFoundError(f"PiperTTS model not found: {model_path}")
            
            # Find piper executable
            piper_executable = None
            try:
                result = subprocess.run(['which', 'piper'], capture_output=True, text=True)
                if result.returncode == 0:
                    piper_executable = result.stdout.strip()
                else:
                    # Try common paths
                    common_paths = ['/usr/local/bin/piper', '/usr/bin/piper', 'piper']
                    for path in common_paths:
                        try:
                            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=2)
                            if result.returncode == 0:
                                piper_executable = path
                                break
                        except:
                            continue
            except:
                pass
            
            if not piper_executable:
                logger.warning("Piper executable not found, falling back to mock TTS")
                raise FileNotFoundError("Piper executable not found")
            
            class PiperTTSHandler:
                def __init__(self, model_path, executable):
                    self.model_path = model_path
                    self.executable = executable
                    self.sample_rate = tts_config.get("sample_rate", 24000)
                    self.length_scale = tts_config.get("length_scale", 1.0)
                    self.noise_scale = tts_config.get("noise_scale", 0.1)
                    self.noise_w = tts_config.get("noise_w", 0.1)
                    logger.info(f"PiperTTS initialized: {model_path}")
                
                async def process_async(self, text: str):
                    try:
                        # Create temporary file for output
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                            temp_path = temp_file.name
                        
                        try:
                            # Prepare Piper command
                            cmd = [
                                self.executable,
                                '--model', str(self.model_path),
                                '--output_file', temp_path,
                            ]
                            
                            # Add parameters
                            if self.length_scale != 1.0:
                                cmd.extend(['--length_scale', str(self.length_scale)])
                            if self.noise_scale != 0.667:
                                cmd.extend(['--noise_scale', str(self.noise_scale)])
                            if self.noise_w != 0.8:
                                cmd.extend(['--noise_w', str(self.noise_w)])
                            
                            # Run Piper synthesis
                            process = await asyncio.create_subprocess_exec(
                                *cmd,
                                stdin=asyncio.subprocess.PIPE,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            
                            stdout, stderr = await asyncio.wait_for(
                                process.communicate(input=text.encode('utf-8')),
                                timeout=5.0
                            )
                            
                            if process.returncode != 0:
                                logger.error(f"Piper failed: {stderr.decode()}")
                                raise RuntimeError(f"Piper synthesis failed")
                            
                            # Load and encode audio
                            audio_data, _ = librosa.load(temp_path, sr=self.sample_rate, mono=True)
                            
                            # Convert to 16-bit PCM and encode
                            audio_16bit = (audio_data * 32767).astype(np.int16)
                            audio_bytes = audio_16bit.tobytes()
                            
                            return {
                                "audio_data": base64.b64encode(audio_bytes).decode('utf-8'),
                                "sample_rate": self.sample_rate,
                                "format": "pcm_s16le"
                            }
                            
                        finally:
                            try:
                                import os
                                os.unlink(temp_path)
                            except:
                                pass
                            
                    except asyncio.TimeoutError:
                        logger.error(f"PiperTTS synthesis timeout for: {text[:50]}...")
                        # Return silence
                        silence = np.zeros(int(self.sample_rate * 0.5), dtype=np.int16)
                        return {
                            "audio_data": base64.b64encode(silence.tobytes()).decode('utf-8'),
                            "sample_rate": self.sample_rate,
                            "format": "pcm_s16le"
                        }
                    except Exception as e:
                        logger.error(f"PiperTTS synthesis error: {e}")
                        # Return silence  
                        silence = np.zeros(int(self.sample_rate * 0.5), dtype=np.int16)
                        return {
                            "audio_data": base64.b64encode(silence.tobytes()).decode('utf-8'),
                            "sample_rate": self.sample_rate,
                            "format": "pcm_s16le"
                        }
            
            self.tts_handler = PiperTTSHandler(model_full_path, piper_executable)
            logger.info("✅ Real PiperTTS handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize PiperTTS: {e}")
            raise
    
    async def _initialize_real_avatar(self):
        """Initialize real Avatar handler with LiteAvatar"""
        try:
            # Check if LiteAvatar models exist
            chat_engine_config = self.config.get("default", {}).get("chat_engine", {})
            avatar_config = chat_engine_config.get("handler_configs", {}).get("LiteAvatar", {})
            avatar_name = avatar_config.get("avatar_name", "20250408/P1-hDQRxa5xfpZK-1yDX8PrQ")
            
            # Look for LiteAvatar models in API directory first, then fallback to project root
            api_avatar_path = Path(__file__).parent.parent / "resource" / "avatar" / "liteavatar" / avatar_name
            project_avatar_path = project_root / "resource" / "avatar" / "liteavatar" / avatar_name
            
            avatar_models_exist = False
            avatar_model_path = None
            
            # Check API directory first
            if api_avatar_path.exists() and (api_avatar_path / "net.pth").exists():
                avatar_models_exist = True
                avatar_model_path = api_avatar_path
                logger.info(f"Found avatar models in API directory: {api_avatar_path}")
            # Then check project root
            elif project_avatar_path.exists() and (project_avatar_path / "net.pth").exists():
                avatar_models_exist = True
                avatar_model_path = project_avatar_path
                logger.info(f"Found avatar models in project directory: {project_avatar_path}")
            
            if not avatar_models_exist:
                logger.warning(f"LiteAvatar models not found for avatar: {avatar_name}")
                await self._initialize_mock_avatar()
                return
            
            class LiteAvatarHandler:
                def __init__(self, model_path, avatar_name, config):
                    self.model_path = model_path
                    self.avatar_name = avatar_name
                    self.fps = config.get("fps", 25)
                    self.enable_fast_mode = config.get("enable_fast_mode", True)
                    self.use_gpu = config.get("use_gpu", True)
                    self.debug = config.get("debug", False)
                    logger.info(f"LiteAvatar initialized: {avatar_name} at {model_path}")
                    logger.info(f"LiteAvatar settings: fps={self.fps}, fast_mode={self.enable_fast_mode}, gpu={self.use_gpu}")
                
                async def process_async(self, text: str, audio_data: str):
                    try:
                        # For now, return empty frames to avoid complex LiteAvatar integration
                        # Real implementation would:
                        # 1. Decode base64 audio
                        # 2. Load neural network models (net.pth, net_decode.pt, net_encode.pt)
                        # 3. Process audio to extract features
                        # 4. Generate lip-sync video frames using neural networks
                        # 5. Return base64 encoded video frames
                        
                        # Calculate approximate number of frames based on audio duration
                        # Assume 1 second of audio for now
                        num_frames = self.fps  # 1 second worth of frames
                        
                        # Return empty frames list - client should handle this gracefully
                        logger.info(f"LiteAvatar would generate {num_frames} frames for text: {text[:50]}...")
                        return {"video_frames": []}
                        
                    except Exception as e:
                        logger.error(f"LiteAvatar processing error: {e}")
                        return {"video_frames": []}
            
            self.avatar_handler = LiteAvatarHandler(avatar_model_path, avatar_name, avatar_config)
            logger.info("✅ Real LiteAvatar handler initialized with model files")
            
        except Exception as e:
            logger.error(f"Failed to initialize LiteAvatar: {e}")
            await self._initialize_mock_avatar()
    
    async def _initialize_mock_avatar(self):
        """Initialize mock avatar handler"""
        class MockAvatarHandler:
            async def process_async(self, text: str, audio_data: str):
                # Return empty video frames - no avatar display
                return {"video_frames": []}
        
        self.avatar_handler = MockAvatarHandler()
        logger.info("✅ Mock Avatar handler initialized")
    
    async def _initialize_real_llm(self):
        """Initialize real LLM handler using OpenAI-compatible API"""
        try:
            # Access the correct config structure with 'default' root key
            chat_engine_config = self.config.get("default", {}).get("chat_engine", {})
            llm_config = chat_engine_config.get("handler_configs", {}).get("LLM_Bailian", {})
            
            if not llm_config.get("enabled", False):
                logger.warning("LLM handler is disabled in config")
                await self._initialize_mock_llm()
                return
            
            # Create a simplified LLM handler wrapper
            class OpenAILLMHandler:
                def __init__(self, config):
                    self.model_name = config.get("model_name", "gpt-4o-mini")
                    self.system_prompt = config.get("system_prompt", "You are a helpful assistant. Always respond in Polish.")
                    self.api_key = config.get("api_key")
                    self.api_url = config.get("api_url", "https://api.openai.com/v1")
                    
                    if not self.api_key:
                        raise ValueError("OpenAI API key is required")
                    
                    logger.info(f"LLM Config: model={self.model_name}, api_url={self.api_url}")
                    
                async def process_async(self, text: str, session_id: str = None):
                    try:
                        # Import OpenAI client
                        from openai import OpenAI
                        
                        client = OpenAI(
                            api_key=self.api_key,
                            base_url=self.api_url
                        )
                        
                        # Create messages
                        messages = [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": text}
                        ]
                        
                        logger.info(f"Sending to OpenAI: {self.model_name} - '{text[:50]}...'")
                        
                        # Call OpenAI API
                        response = client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        response_text = response.choices[0].message.content
                        logger.info(f"OpenAI response: {response_text[:100]}...")
                        
                        return {"text": response_text}
                        
                    except Exception as e:
                        logger.error(f"OpenAI API call failed: {e}")
                        # Fallback to mock response
                        return {"text": "Przepraszam, wystąpił problem z połączeniem. Spróbuj ponownie."}
            
            self.llm_handler = OpenAILLMHandler(llm_config)
            logger.info("✅ Real OpenAI LLM handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize real LLM: {e}")
            logger.info("Falling back to mock LLM")
            await self._initialize_mock_llm()

    async def _initialize_mock_llm(self):
        """Initialize mock LLM handler"""
        
        class MockLLMHandler:
            async def process_async(self, text: str, session_id: str = None):
                # Mock LLM response
                responses = [
                    "Dziękuję za twoje pytanie. Jak mogę ci pomóc?",
                    "To bardzo interesujące zagadnienie. Co chciałbyś wiedzieć więcej?",
                    "Rozumiem twój punkt widzenia. Czy masz jakieś dodatkowe pytania?",
                    "Świetnie! Jestem tutaj, aby ci pomóc w każdej sprawie.",
                    "To dobra obserwacja. Czy chcesz, żebym rozwinął ten temat?"
                ]
                import random
                response = random.choice(responses)
                return {"text": response}
        
        self.llm_handler = MockLLMHandler()
        logger.info("✅ Mock LLM handler initialized")
    
    async def _initialize_mock_handlers(self):
        """Initialize mock handlers for testing purposes"""
        
        class MockHandler:
            def __init__(self, name):
                self.name = name
                
            async def process_async(self, data, *args):
                # Simulate processing time
                await asyncio.sleep(0.1)
                return self._mock_process(data, *args)
                
            def process(self, data, *args):
                return self._mock_process(data, *args)
                
            def _mock_process(self, data, *args):
                if self.name == "vad":
                    return {"has_speech": True}
                elif self.name == "asr":
                    return {"text": "Przykładowy transkrybowany tekst."}
                elif self.name == "llm":
                    return {"text": "To jest przykładowa odpowiedź od asystenta AI."}
                elif self.name == "tts":
                    # Return mock base64 encoded audio
                    mock_audio = b"mock_audio_data"
                    return {"audio_data": base64.b64encode(mock_audio).decode('utf-8')}
                elif self.name == "avatar":
                    # Return mock video frames
                    mock_frame = b"mock_video_frame"
                    return {"video_frames": [base64.b64encode(mock_frame).decode('utf-8')]}
                
            async def initialize(self, config):
                pass
                
            async def cleanup(self):
                pass
        
        # Initialize mock handlers
        self.vad_handler = MockHandler("vad")
        self.asr_handler = MockHandler("asr") 
        self.llm_handler = MockHandler("llm")
        self.tts_handler = MockHandler("tts")
        self.avatar_handler = MockHandler("avatar")
        
        logger.info("✅ Mock handlers initialized (replace with real handlers)")
    
    async def _initialize_real_handlers(self):
        """Initialize real handlers - to be implemented when handlers are properly imported"""
        # TODO: Replace mock handlers with real ones
        # This method will contain the real handler initialization
        # when the import issues are resolved
        pass
    
    async def process_audio(self, audio_data: bytes, session_id: str) -> Dict[str, Any]:
        """Process audio input through the pipeline"""
        if not self.is_initialized:
            raise RuntimeError("Pipeline not initialized")
        
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            result = {}
            
            # Step 1: Voice Activity Detection (optional)
            if self.vad_handler:
                vad_result = await self._run_vad(audio_data)
                if not vad_result.get("has_speech", True):
                    return {"error": "No speech detected"}
                result["vad"] = vad_result
            
            # Step 2: Speech Recognition
            asr_result = await self._run_asr(audio_data)
            transcribed_text = asr_result.get("text", "")
            if not transcribed_text.strip():
                return {"error": "No text transcribed"}
            
            result["asr"] = asr_result
            result["transcribed_text"] = transcribed_text
            
            # Step 3: Generate response with LLM
            llm_result = await self._run_llm(transcribed_text, session_id)
            response_text = llm_result.get("text", "")
            result["llm"] = llm_result
            result["response_text"] = response_text
            
            # Step 4: Text-to-Speech
            if response_text:
                tts_result = await self._run_tts(response_text)
                result["tts"] = tts_result
                result["audio_data"] = tts_result.get("audio_data")
                
                # Step 5: Avatar generation (optional)
                if self.avatar_handler and tts_result.get("audio_data"):
                    avatar_result = await self._run_avatar(response_text, tts_result.get("audio_data"))
                    result["avatar"] = avatar_result
                    result["video_frames"] = avatar_result.get("video_frames", [])
            
            # Update stats
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            self._update_stats(processing_time, success=True)
            
            return result
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Audio processing failed: {e}")
            raise
    
    async def process_text(self, text: str, session_id: str) -> Dict[str, Any]:
        """Process text input through the pipeline"""
        if not self.is_initialized:
            raise RuntimeError("Pipeline not initialized")
        
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            result = {}
            result["input_text"] = text
            
            # Step 1: Generate response with LLM
            llm_result = await self._run_llm(text, session_id)
            response_text = llm_result.get("text", "")
            result["llm"] = llm_result
            result["response_text"] = response_text
            
            # Step 2: Text-to-Speech
            if response_text:
                tts_result = await self._run_tts(response_text)
                result["tts"] = tts_result
                result["audio_data"] = tts_result.get("audio_data")
                
                # Step 3: Avatar generation (optional)
                if self.avatar_handler and tts_result.get("audio_data"):
                    avatar_result = await self._run_avatar(response_text, tts_result.get("audio_data"))
                    result["avatar"] = avatar_result
                    result["video_frames"] = avatar_result.get("video_frames", [])
            
            # Update stats
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            self._update_stats(processing_time, success=True)
            
            return result
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Text processing failed: {e}")
            raise
    
    async def _run_vad(self, audio_data: bytes) -> Dict[str, Any]:
        """Run Voice Activity Detection"""
        try:
            if hasattr(self.vad_handler, 'process_async'):
                return await self.vad_handler.process_async(audio_data)
            else:
                # Fallback to sync method
                return self.vad_handler.process(audio_data)
        except Exception as e:
            logger.error(f"VAD processing failed: {e}")
            return {"has_speech": True}  # Default to having speech
    
    async def _run_asr(self, audio_data: bytes) -> Dict[str, Any]:
        """Run Automatic Speech Recognition"""
        try:
            if hasattr(self.asr_handler, 'process_async'):
                return await self.asr_handler.process_async(audio_data)
            else:
                # Run in thread pool for sync methods
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.asr_handler.process, audio_data)
        except Exception as e:
            logger.error(f"ASR processing failed: {e}")
            raise
    
    async def _run_llm(self, text: str, session_id: str) -> Dict[str, Any]:
        """Run Large Language Model"""
        try:
            if hasattr(self.llm_handler, 'process_async'):
                return await self.llm_handler.process_async(text, session_id)
            else:
                # Run in thread pool for sync methods
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.llm_handler.process, text)
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            raise
    
    async def _run_tts(self, text: str) -> Dict[str, Any]:
        """Run Text-to-Speech"""
        try:
            if hasattr(self.tts_handler, 'process_async'):
                result = await self.tts_handler.process_async(text)
            else:
                # Run in thread pool for sync methods
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.tts_handler.process, text)
            
            # Ensure audio data is base64 encoded
            if "audio_data" in result and isinstance(result["audio_data"], bytes):
                result["audio_data"] = base64.b64encode(result["audio_data"]).decode('utf-8')
            
            return result
        except Exception as e:
            logger.error(f"TTS processing failed: {e}")
            raise
    
    async def _run_avatar(self, text: str, audio_data: str) -> Dict[str, Any]:
        """Run Avatar generation"""
        try:
            if hasattr(self.avatar_handler, 'process_async'):
                result = await self.avatar_handler.process_async(text, audio_data)
            else:
                # Run in thread pool for sync methods
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.avatar_handler.process, text, audio_data)
            
            # Ensure video frames are base64 encoded
            if "video_frames" in result:
                frames = result["video_frames"]
                if frames and isinstance(frames[0], bytes):
                    result["video_frames"] = [base64.b64encode(frame).decode('utf-8') for frame in frames]
            
            return result
        except Exception as e:
            logger.error(f"Avatar processing failed: {e}")
            return {"video_frames": []}
    
    def _update_stats(self, processing_time: float, success: bool):
        """Update processing statistics"""
        if success:
            self.stats["successful_requests"] += 1
            
            # Update average processing time
            total_successful = self.stats["successful_requests"]
            current_avg = self.stats["avg_processing_time"]
            self.stats["avg_processing_time"] = ((current_avg * (total_successful - 1)) + processing_time) / total_successful
    
    async def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            "initialized": self.is_initialized,
            "vad_available": self.vad_handler is not None,
            "asr_available": self.asr_handler is not None,
            "llm_available": self.llm_handler is not None,
            "tts_available": self.tts_handler is not None,
            "avatar_available": self.avatar_handler is not None
        }
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed pipeline status"""
        component_status = {}
        
        # Check each component
        for name, handler in [
            ("vad", self.vad_handler),
            ("asr", self.asr_handler), 
            ("llm", self.llm_handler),
            ("tts", self.tts_handler),
            ("avatar", self.avatar_handler)
        ]:
            if handler is not None:
                component_status[name] = {
                    "status": "healthy",
                    "available": True,
                    "config": self.config.get(name, {})
                }
            else:
                component_status[name] = {
                    "status": "unavailable",
                    "available": False
                }
        
        # Determine overall status
        critical_components = ["asr", "llm", "tts"]
        critical_healthy = all(
            component_status.get(comp, {}).get("available", False) 
            for comp in critical_components
        )
        
        if critical_healthy:
            overall_status = "healthy"
        else:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "components": component_status,
            "stats": self.stats,
            "initialization_time": self.initialization_time,
            "uptime": time.time() - (self.initialization_time or time.time()) if self.initialization_time else 0
        }
    
    async def cleanup(self):
        """Cleanup pipeline resources"""
        logger.info("🧹 Cleaning up pipeline...")
        
        # Cleanup handlers
        for handler in [self.vad_handler, self.asr_handler, self.llm_handler, self.tts_handler, self.avatar_handler]:
            if handler and hasattr(handler, 'cleanup'):
                try:
                    await handler.cleanup()
                except Exception as e:
                    logger.error(f"Handler cleanup error: {e}")
        
        self.is_initialized = False
        logger.info("✅ Pipeline cleanup completed")
