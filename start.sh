#!/bin/bash
set -e

echo "=== NetViz Startup ==="

# Check for .env file
if [ ! -f backend/.env ]; then
    echo "WARNING: backend/.env not found. Copy backend/.env.example to backend/.env and configure it."
fi

# Start services
echo "Starting services with Docker Compose..."
docker compose up -d

echo ""
echo "=== Services Started ==="
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:3001"
echo "Health:   http://localhost:3001/health"
echo ""
echo "Use 'docker compose logs -f' to view logs"
echo "Use 'docker compose down' to stop services"
