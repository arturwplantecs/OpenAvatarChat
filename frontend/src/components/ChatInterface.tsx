'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff } from 'lucide-react'

interface Message {
  id: string
  text: string
  sender: 'user' | 'avatar'
  timestamp: Date
}

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (text: string) => void
  isConnected: boolean
}

export default function ChatInterface({ messages, onSendMessage, isConnected }: ChatInterfaceProps) {
  const [inputText, setInputText] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)

  // Debug logging
  useEffect(() => {
    console.log('ChatInterface received messages:', messages)
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendText = () => {
    if (inputText.trim() && isConnected) {
      onSendMessage(inputText.trim())
      setInputText('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendText()
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder

      const chunks: BlobPart[] = []
      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data)
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        // TODO: Send audio to backend for speech-to-text processing
        console.log('Audio recorded:', audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-blue-500 text-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Chat with Avatar</h2>
        <div className="flex items-center mt-1">
          <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
          <span className="text-sm opacity-90">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>Start a conversation with your avatar!</p>
            <p className="text-sm mt-1">Type a message or use voice input</p>
          </div>
        ) : (
          <div>
            {/* Debug info */}
            <div className="text-xs text-gray-500 mb-2">Messages: {messages.length}</div>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex mb-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {formatTime(message.timestamp)} - {message.sender}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-white dark:bg-gray-800 p-4">
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Type your message..." : "Connecting..."}
              disabled={!isConnected}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
              rows={1}
            />
          </div>
          
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={!isConnected}
            className={`p-2 rounded-lg transition-colors ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={isRecording ? 'Stop recording' : 'Start voice recording'}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          <button
            onClick={handleSendText}
            disabled={!inputText.trim() || !isConnected}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white p-2 rounded-lg transition-colors"
            title="Send message"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}
