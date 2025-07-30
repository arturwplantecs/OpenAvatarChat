'use client'

import { useState, useEffect, useRef } from 'react'
import AvatarDisplay from '@/components/AvatarDisplay'
import WebcamPiP from '@/components/WebcamPiP'
import ChatInterface from '@/components/ChatInterface'
import ControlPanel from '@/components/ControlPanel'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useLiveAvatar } from '@/hooks/useLiveAvatar'

export default function Home() {
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [volume, setVolume] = useState(50)
  const [showWebcam, setShowWebcam] = useState(true)
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'avatar', timestamp: Date}>>([])
  const [avatarVideoData, setAvatarVideoData] = useState<string | undefined>()
  // Debug: Log messages state changes
  useEffect(() => {
    console.log('Main page messages state updated:', messages)
  }, [messages])
  
  const { socket, isConnected: wsConnected, sendMessage } = useWebSocket()
  const { 
    avatarRef, 
    isAvatarLoaded, 
    initializeAvatar, 
    sendMessage: sendAvatarMessage,
    isListening 
  } = useLiveAvatar()

  useEffect(() => {
    setIsConnected(wsConnected)
  }, [wsConnected])

  // Auto-initialize avatar when component mounts
  useEffect(() => {
    initializeAvatar()
  }, [initializeAvatar])

  useEffect(() => {
    const handleWebSocketMessage = (event: CustomEvent) => {
      const data = event.detail
      console.log('Processing WebSocket message:', data)
      
      if (data.type === 'avatar_response') {
        const newMessage = {
          id: Date.now().toString(),
          text: data.text,
          sender: 'avatar' as const,
          timestamp: new Date()
        }
        console.log('Adding avatar message:', newMessage)
        setMessages(prev => [...prev, newMessage])
      } else if (data.type === 'avatar_video') {
        // Update avatar video frame
        console.log('Received avatar video frame')
        setAvatarVideoData(data.video_data)
      }
    }

    window.addEventListener('websocket-message', handleWebSocketMessage as EventListener)
    
    return () => {
      window.removeEventListener('websocket-message', handleWebSocketMessage as EventListener)
    }
  }, [])

  const handleSendMessage = (text: string) => {
    const newMessage = {
      id: Date.now().toString(),
      text,
      sender: 'user' as const,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, newMessage])
    
    // Send to backend using native WebSocket
    if (sendMessage) {
      sendMessage({ 
        type: 'user_message', 
        text,
        timestamp: Date.now()
      })
    }
    
    // Send to avatar
    if (sendAvatarMessage) {
      sendAvatarMessage(text)
    }
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume)
  }

  return (
    <main className="h-screen w-screen relative bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Debug overlay - Top Left */}
      <div className="fixed top-4 left-4 bg-black/80 text-white p-2 rounded text-xs z-50">
        <div>Connected: {isConnected ? '✅' : '❌'}</div>
        <div>Avatar: {isAvatarLoaded ? '✅' : '❌'}</div>
        <div>Messages: {messages.length}</div>
      </div>

      {/* Avatar Display - Center */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
        <AvatarDisplay 
          ref={avatarRef}
          isLoaded={isAvatarLoaded}
          isListening={isListening}
          volume={volume}
          isMuted={isMuted}
          videoData={avatarVideoData}
        />
      </div>

      {/* Webcam Picture-in-Picture - Bottom Right */}
      {showWebcam && (
        <WebcamPiP 
          onClose={() => setShowWebcam(false)}
        />
      )}

      {/* Chat Interface - Right Side */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm shadow-lg z-20">
        <ChatInterface 
          messages={messages}
          onSendMessage={handleSendMessage}
          isConnected={isConnected}
        />
      </div>

      {/* Control Panel - Bottom Center */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-30">
        <ControlPanel
          isMuted={isMuted}
          volume={volume}
          isConnected={isConnected}
          isListening={isListening}
          showWebcam={showWebcam}
          onToggleMute={toggleMute}
          onVolumeChange={handleVolumeChange}
          onToggleWebcam={() => setShowWebcam(!showWebcam)}
        />
      </div>
    </main>
  )
}
