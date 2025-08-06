#!/usr/bin/env python3
"""
Simple client example for OpenAvatarChat API
"""

import requests
import json
import base64
import asyncio
import websockets
from typing import Dict, Any


class OpenAvatarChatClient:
    """Simple client for OpenAvatarChat API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def create_session(self) -> str:
        """Create a new chat session"""
        response = requests.post(f"{self.base_url}/api/v1/sessions")
        response.raise_for_status()
        
        data = response.json()
        self.session_id = data["session_id"]
        print(f"✅ Created session: {self.session_id}")
        return self.session_id
    
    def send_text(self, text: str) -> Dict[str, Any]:
        """Send text message via HTTP"""
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        response = requests.post(
            f"{self.base_url}/api/v1/sessions/{self.session_id}/text",
            json={"text": text}
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"📤 Sent: {text}")
        print(f"📥 Response: {result.get('response', 'No response')}")
        
        # Decode audio if present
        if result.get("audio_data"):
            audio_bytes = base64.b64decode(result["audio_data"])
            print(f"🔊 Audio data received: {len(audio_bytes)} bytes")
        
        # Decode video frames if present
        if result.get("video_frames"):
            frames = result["video_frames"]
            print(f"🎥 Video frames received: {len(frames)} frames")
        
        return result
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        if not self.session_id:
            raise ValueError("No active session.")
        
        response = requests.get(f"{self.base_url}/api/v1/sessions/{self.session_id}")
        response.raise_for_status()
        return response.json()
    
    def end_session(self):
        """End the current session"""
        if not self.session_id:
            return
        
        response = requests.delete(f"{self.base_url}/api/v1/sessions/{self.session_id}")
        response.raise_for_status()
        
        print(f"🗑️ Ended session: {self.session_id}")
        self.session_id = None
    
    def get_health(self) -> Dict[str, Any]:
        """Get API health status"""
        response = requests.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    async def chat_websocket(self, messages: list):
        """Chat via WebSocket for real-time communication"""
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        ws_url = f"ws://127.0.0.1:8000/api/v1/sessions/{self.session_id}/ws"
        
        async with websockets.connect(ws_url) as websocket:
            print(f"🔌 Connected to WebSocket")
            
            # Send messages
            for message in messages:
                await websocket.send(json.dumps({
                    "type": "text_message",
                    "text": message
                }))
                print(f"📤 Sent: {message}")
                
                # Receive response
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("type") == "text_processed":
                    print(f"📥 Response: {data.get('response_text', 'No response')}")
                    if data.get("audio_data"):
                        print(f"🔊 Audio received")
                    if data.get("video_frames"):
                        print(f"🎥 Video frames: {len(data['video_frames'])}")
                elif data.get("type") == "error":
                    print(f"❌ Error: {data.get('message', 'Unknown error')}")


def main():
    """Example usage"""
    client = OpenAvatarChatClient()
    
    # Test health
    print("🏥 Testing health endpoint...")
    health = client.get_health()
    print(f"Health: {health['status']}")
    print()
    
    # Create session
    print("📋 Creating session...")
    client.create_session()
    print()
    
    # Send text messages
    print("💬 Testing text messages...")
    messages = [
        "Cześć! Jak się masz?",
        "Opowiedz mi coś o sobie.",
        "Co potrafisz robić?"
    ]
    
    for message in messages:
        result = client.send_text(message)
        print()
    
    # Test WebSocket (comment out if not needed)
    print("🔌 Testing WebSocket...")
    try:
        asyncio.run(client.chat_websocket([
            "To jest test WebSocket",
            "Czy słyszysz mnie?"
        ]))
    except Exception as e:
        print(f"WebSocket test failed: {e}")
    print()
    
    # Get session info
    print("📊 Getting session info...")
    session_info = client.get_session_info()
    print(f"Session status: {session_info['status']}")
    print()
    
    # End session
    print("🔚 Ending session...")
    client.end_session()


if __name__ == "__main__":
    main()
