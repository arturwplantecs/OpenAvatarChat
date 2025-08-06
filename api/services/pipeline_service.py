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
            # For now, create mock handlers that will be replaced with actual ones
            # This allows the API to start and be tested
            await self._initialize_mock_handlers()
            
        except Exception as e:
            logger.error(f"Handler initialization failed: {e}")
            raise
    
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
