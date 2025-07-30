'use client'

import { useEffect, useState, useRef } from 'react'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export function useWebSocket() {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = () => {
    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8282'
      const clientId = Math.random().toString(36).substring(7)
      const ws = new WebSocket(`${wsUrl}/ws/${clientId}`)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        reconnectAttempts.current = 0
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        setSocket(null)
        
        // Attempt to reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          console.log(`Reconnecting... attempt ${reconnectAttempts.current}`)
          setTimeout(connect, 1000 * reconnectAttempts.current)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('WebSocket connection error')
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('Received message:', message)
          
          // Dispatch custom event for message handling
          const customEvent = new CustomEvent('websocket-message', { detail: message })
          window.dispatchEvent(customEvent)
          console.log('Dispatched websocket-message event:', message)
        } catch (err) {
          console.error('Error parsing message:', err)
        }
      }

      setSocket(ws)
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      setError('Failed to create WebSocket connection')
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [])

  const sendMessage = (message: WebSocketMessage) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  return {
    socket,
    isConnected,
    error,
    sendMessage
  }
}
