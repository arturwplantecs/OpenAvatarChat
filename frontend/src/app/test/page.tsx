'use client'

import { useState, useEffect } from 'react'
import { useWebSocket } from '@/hooks/useWebSocket'

export default function TestPage() {
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: string, timestamp: Date}>>([])
  const [inputText, setInputText] = useState('')
  const { isConnected, sendMessage } = useWebSocket()

  useEffect(() => {
    const handleWebSocketMessage = (event: CustomEvent) => {
      const data = event.detail
      console.log('Test page received message:', data)
      
      if (data.type === 'avatar_response') {
        const newMessage = {
          id: Date.now().toString(),
          text: data.text,
          sender: 'avatar',
          timestamp: new Date()
        }
        console.log('Test page adding message:', newMessage)
        setMessages(prev => {
          const updated = [...prev, newMessage]
          console.log('Updated messages array:', updated)
          return updated
        })
      }
    }

    window.addEventListener('websocket-message', handleWebSocketMessage as EventListener)
    
    return () => {
      window.removeEventListener('websocket-message', handleWebSocketMessage as EventListener)
    }
  }, [])

  const handleSend = () => {
    if (inputText.trim() && isConnected) {
      const userMessage = {
        id: Date.now().toString(),
        text: inputText.trim(),
        sender: 'user',
        timestamp: new Date()
      }
      
      console.log('Adding user message:', userMessage)
      setMessages(prev => {
        const updated = [...prev, userMessage]
        console.log('Updated messages with user message:', updated)
        return updated
      })
      
      sendMessage({ 
        type: 'user_message', 
        text: inputText.trim(),
        timestamp: Date.now()
      })
      
      setInputText('')
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">WebSocket Test Page</h1>
      
      <div className="mb-4">
        <div className={`w-4 h-4 rounded-full inline-block mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>

      <div className="mb-4">
        <h2 className="text-lg font-semibold mb-2">Messages ({messages.length}):</h2>
        <div className="border border-gray-300 rounded p-4 h-64 overflow-y-auto bg-gray-50">
          {messages.length === 0 ? (
            <p className="text-gray-500">No messages yet...</p>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`mb-2 p-2 rounded ${message.sender === 'user' ? 'bg-blue-100 ml-8' : 'bg-gray-200 mr-8'}`}>
                <div className="font-semibold text-sm">{message.sender}</div>
                <div>{message.text}</div>
                <div className="text-xs text-gray-500">{message.timestamp.toLocaleTimeString()}</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          className="flex-1 border border-gray-300 rounded px-3 py-2"
          disabled={!isConnected}
        />
        <button
          onClick={handleSend}
          disabled={!isConnected || !inputText.trim()}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-300"
        >
          Send
        </button>
      </div>
    </div>
  )
}
