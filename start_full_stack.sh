#!/bin/bash

# Start the Python backend
echo "Starting Python backend..."
cd /home/arti/Repos/OpenAvatarChat
python api/main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start the Next.js frontend
echo "Starting Next.js frontend..."
cd /home/arti/Repos/OpenAvatarChat/frontend-nextjs
npm run dev &
FRONTEND_PID=$!

# Function to cleanup processes
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

echo "✅ Backend started on https://localhost:8282"
echo "✅ Frontend started on http://localhost:3000"
echo "Press Ctrl+C to stop both services"

# Wait for both processes
wait
