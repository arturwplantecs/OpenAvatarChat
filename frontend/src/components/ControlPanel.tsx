'use client'

import { Volume2, VolumeX, Mic, MicOff, Video, VideoOff, Wifi, WifiOff } from 'lucide-react'

interface ControlPanelProps {
  isMuted: boolean
  volume: number
  isConnected: boolean
  isListening: boolean
  showWebcam: boolean
  onToggleMute: () => void
  onVolumeChange: (volume: number) => void
  onToggleWebcam: () => void
}

export default function ControlPanel({
  isMuted,
  volume,
  isConnected,
  isListening,
  showWebcam,
  onToggleMute,
  onVolumeChange,
  onToggleWebcam
}: ControlPanelProps) {
  return (
    <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg border border-gray-200 dark:border-gray-600">
      <div className="flex items-center space-x-4">
        {/* Connection Status */}
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <Wifi className="w-5 h-5 text-green-500" />
          ) : (
            <WifiOff className="w-5 h-5 text-red-500" />
          )}
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
            {isConnected ? 'Connected' : 'Offline'}
          </span>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600"></div>

        {/* Microphone Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleMute}
            className={`p-2 rounded-full transition-colors ${
              isMuted 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
          
          {isListening && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-600 dark:text-green-400 font-medium">Listening</span>
            </div>
          )}
        </div>

        {/* Volume Controls */}
        <div className="flex items-center space-x-2">
          <Volume2 className="w-4 h-4 text-gray-600 dark:text-gray-300" />
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => onVolumeChange(parseInt(e.target.value))}
            className="w-20 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <span className="text-xs text-gray-600 dark:text-gray-300 w-8 text-center">
            {volume}%
          </span>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600"></div>

        {/* Webcam Controls */}
        <button
          onClick={onToggleWebcam}
          className={`p-2 rounded-full transition-colors ${
            showWebcam 
              ? 'bg-blue-500 hover:bg-blue-600 text-white' 
              : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200'
          }`}
          title={showWebcam ? 'Hide webcam' : 'Show webcam'}
        >
          {showWebcam ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
        </button>
      </div>
    </div>
  )
}
