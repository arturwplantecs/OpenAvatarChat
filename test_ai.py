#!/usr/bin/env python3
"""
Test script to verify QUARI AI functionality
"""

import asyncio
import websockets
import json
import time

async def test_ai_chat():
    """Test the AI chat functionality"""
    
    print("🧪 Testing QUARI AI Chat...")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8282/ws/test_client"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📥 Welcome: {welcome_data}")
            
            if not welcome_data.get('chat_engine_ready', False):
                print("❌ Chat engine not ready!")
                return False
            
            # Send test message in Polish
            test_message = {
                "type": "user_message",
                "text": "Cześć! Jak masz na imię?",
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"📤 Sending: {test_message['text']}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            print("⏳ Waiting for AI response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            response_data = json.loads(response)
            print(f"📥 Response: {response_data}")
            
            # Check if we got a real AI response (not echo)
            response_text = response_data.get('text', '')
            if 'Echo' in response_text or 'Processing:' in response_text or 'Message sent to AI' in response_text:
                print(f"⏳ Got intermediate response, waiting for actual AI response...")
                # Wait for the actual AI response
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                response_data = json.loads(response)
                print(f"📥 AI Response: {response_data}")
                response_text = response_data.get('text', '')
            
            if 'Echo' in response_text or 'Processing:' in response_text or 'Message sent to AI' in response_text:
                print("❌ Still got echo/processing response instead of AI response")
                return False
            
            print("✅ AI responded successfully!")
            return True
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for AI response")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_ai_chat())
    if result:
        print("\n🎉 QUARI AI is working correctly!")
    else:
        print("\n💔 QUARI AI test failed. Check the configuration.")
