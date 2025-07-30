'use client'

import { useState, useRef, useEffect } from 'react'

interface WebcamPiPProps {
  onClose: () => void
}

export default function WebcamPiP({ onClose }: WebcamPiPProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [isVisible, setIsVisible] = useState(true)
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Initialize webcam
    const initWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240 },
          audio: false
        })
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (error) {
        console.error('Error accessing webcam:', error)
      }
    }

    if (isVisible) {
      initWebcam()
    }

    return () => {
      // Cleanup
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [isVisible])

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return
    
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const toggleVisibility = () => {
    setIsVisible(!isVisible)
  }

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={toggleVisibility}
          className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg transition-colors"
          title="Show webcam"
        >
          📹
        </button>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="pip-container bg-black rounded-lg overflow-hidden shadow-lg"
      style={{
        transform: `translate(${position.x}px, ${position.y}px)`,
        cursor: isDragging ? 'grabbing' : 'grab'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Controls Overlay */}
      <div className="absolute top-2 right-2 z-10 flex space-x-1">
        <button
          onClick={toggleVisibility}
          className="bg-black/50 hover:bg-black/70 text-white p-1 rounded text-xs transition-colors"
          title="Hide webcam"
        >
          👁️
        </button>
        <button
          onClick={onClose}
          className="bg-red-500/70 hover:bg-red-500 text-white p-1 rounded text-xs transition-colors"
          title="Close webcam"
        >
          ✕
        </button>
      </div>

      {/* Video Element */}
      <video
        ref={videoRef}
        className="pip-video"
        autoPlay
        playsInline
        muted
      />

      {/* Resize Handle */}
      <div className="absolute bottom-0 right-0 w-4 h-4 bg-gray-400/50 cursor-se-resize">
        <div className="absolute bottom-1 right-1 w-2 h-2 bg-white/70 rounded-full"></div>
      </div>
    </div>
  )
}
