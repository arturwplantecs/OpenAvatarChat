'use client'

import { forwardRef, useEffect, useRef } from 'react'

interface AvatarDisplayProps {
  isLoaded: boolean
  isListening: boolean
  volume: number
  isMuted: boolean
  videoData?: string  // Base64 encoded video frame
}

const AvatarDisplay = forwardRef<HTMLDivElement, AvatarDisplayProps>(
  ({ isLoaded, isListening, volume, isMuted, videoData }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    
    // Update canvas when new video data arrives
    useEffect(() => {
      if (videoData && canvasRef.current) {
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')
        if (ctx) {
          try {
            // Create image from base64 data
            const img = new Image()
            img.onload = () => {
              // Clear canvas and draw new frame
              ctx.clearRect(0, 0, canvas.width, canvas.height)
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
            }
            img.src = `data:image/jpeg;base64,${videoData}`
          } catch (error) {
            console.error('Error updating avatar video:', error)
          }
        }
      }
    }, [videoData])
    return (
      <div 
        ref={ref}
        className="relative w-full max-w-md h-96 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden shadow-xl"
      >
        {/* Avatar Container */}
        <div className="w-full h-full flex items-center justify-center">
          {!isLoaded ? (
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              <p className="text-gray-600 dark:text-gray-300">Loading Avatar...</p>
            </div>
          ) : (
            <div className="w-full h-full relative flex items-center justify-center">
              {videoData ? (
                // Live avatar video display
                <canvas 
                  ref={canvasRef}
                  className="w-full h-full object-cover rounded-lg"
                  width={512}
                  height={512}
                />
              ) : (
                // Fallback placeholder
                <div className="w-full h-full bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 flex items-center justify-center">
                  <div className="text-center">
                    <div className={`w-32 h-32 rounded-full bg-blue-500 mx-auto mb-4 flex items-center justify-center text-white text-4xl ${isListening ? 'animate-pulse' : ''}`}>
                      🤖
                    </div>
                    <p className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                      LiveAvatar
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {isListening ? 'Listening...' : 'Ready to chat'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Status Indicators */}
        <div className="absolute top-4 right-4 flex space-x-2">
          {isMuted && (
            <div className="bg-red-500 text-white p-2 rounded-full text-xs">
              🔇
            </div>
          )}
          {isListening && (
            <div className="bg-green-500 text-white p-2 rounded-full text-xs animate-pulse">
              🎤
            </div>
          )}
        </div>

        {/* Volume Indicator */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-black/20 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-200"
              style={{ width: `${volume}%` }}
            ></div>
          </div>
        </div>
      </div>
    )
  }
)

AvatarDisplay.displayName = 'AvatarDisplay'

export default AvatarDisplay
