#!/bin/bash

# Otomeshon Development Server Startup Script
# This script starts both the backend and frontend development servers

set -e

echo "🚀 Starting Otomeshon Development Environment..."
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the Vellum repository root directory"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    pkill -f "python.*main_simple" 2>/dev/null || true
    pkill -f "node.*dev" 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting backend server..."
cd backend
python app/main_simple.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend server is running at http://localhost:8000"
        echo "📖 API Documentation: http://localhost:8000/docs"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend failed to start after 10 seconds"
        cleanup
        exit 1
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..15}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend server is running at http://localhost:3000"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Frontend failed to start after 15 seconds"
        cleanup
        exit 1
    fi
    sleep 1
done

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📍 Services:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "💡 Tips:"
echo "   - Press Ctrl+C to stop both servers"
echo "   - Backend includes 100 sample records for testing"
echo "   - Frontend supports hot reloading for development"
echo ""
echo "🔍 Monitoring logs... (Press Ctrl+C to stop)"

# Wait for user to stop the servers
wait