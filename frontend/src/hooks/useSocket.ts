'use client'

import { useEffect, useState } from 'react'
import { io, Socket } from 'socket.io-client'

export function useSocket() {
  const [socket, setSocket] = useState<Socket | null>(null)

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8282'
    
    const socketInstance = io(wsUrl, {
      transports: ['websocket', 'polling'],
      upgrade: true,
    })

    socketInstance.on('connect', () => {
      console.log('Connected to backend:', socketInstance.id)
    })

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from backend')
    })

    socketInstance.on('connect_error', (error) => {
      console.error('Connection error:', error)
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.close()
    }
  }, [])

  return socket
}
