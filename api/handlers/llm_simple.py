"""
Simple LLM handler with conversation history support
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class SimpleLLMHandler:
    """Simple LLM handler that supports conversation history"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name", "gpt-4o-mini")
        self.api_key = config.get("api_key")
        self.api_url = config.get("api_url", "https://api.openai.com/v1")
        self.system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
        
        if not self.api_key:
            raise ValueError("API key is required for LLM handler")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )
        
        logger.info(f"✅ Simple LLM handler initialized with model: {self.model_name}")
    
    async def process_async(self, text: str, session_id: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process text with conversation history"""
        try:
            # Build messages array
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": text})
            
            logger.info(f"🧠 LLM processing with {len(messages)} messages (including system prompt)")
            logger.debug(f"Messages: {messages}")
            
            # Make API call
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
            )
            
            response_text = completion.choices[0].message.content
            
            logger.info(f"✅ LLM response: {response_text[:100]}...")
            
            return {
                "response_text": response_text,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"❌ LLM processing failed: {e}")
            raise
    
    def process(self, text: str) -> Dict[str, Any]:
        """Synchronous process method (fallback)"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            
            return {
                "response_text": response_text
            }
            
        except Exception as e:
            logger.error(f"❌ LLM processing failed: {e}")
            raise
