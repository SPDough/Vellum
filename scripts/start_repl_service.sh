#!/bin/bash

# Script to start the Docker Python REPL service for LangChain workflows
# This script builds and runs the secure Python REPL container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPL_DIR="$PROJECT_ROOT/docker/python-repl"
NETWORK_NAME="otomeshon-network"
CONTAINER_NAME="otomeshon-python-repl"
SERVICE_PORT="8001"

echo -e "${BLUE}Starting Docker Python REPL Service for Otomeshon...${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Create network if it doesn't exist
if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo -e "${YELLOW}Creating Docker network: $NETWORK_NAME${NC}"
    docker network create "$NETWORK_NAME"
else
    echo -e "${GREEN}Docker network $NETWORK_NAME already exists${NC}"
fi

# Stop and remove existing container if running
if docker ps -a --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo -e "${YELLOW}Stopping existing container: $CONTAINER_NAME${NC}"
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# Change to REPL directory
cd "$REPL_DIR"

# Build the Docker image
echo -e "${BLUE}Building Python REPL Docker image...${NC}"
docker build -t otomeshon-python-repl:latest .

# Start the service using docker-compose
echo -e "${BLUE}Starting Python REPL service...${NC}"
docker-compose up -d

# Wait for service to be healthy
echo -e "${BLUE}Waiting for service to be ready...${NC}"
for i in {1..30}; do
    if curl -s -f "http://localhost:$SERVICE_PORT/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Python REPL service is healthy and ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Service failed to start or is not responding${NC}"
        echo -e "${YELLOW}Check logs with: docker logs $CONTAINER_NAME${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Waiting... ($i/30)${NC}"
    sleep 2
done

# Get service info
echo -e "${BLUE}Getting service information...${NC}"
if curl -s "http://localhost:$SERVICE_PORT/capabilities" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}Service capabilities:${NC}"
    curl -s "http://localhost:$SERVICE_PORT/capabilities" | jq .
else
    echo -e "${YELLOW}Service is running but capabilities endpoint not available${NC}"
fi

# Display connection info
echo ""
echo -e "${GREEN}🎉 Python REPL Service Started Successfully!${NC}"
echo -e "${BLUE}Service URL:${NC} http://localhost:$SERVICE_PORT"
echo -e "${BLUE}Health Check:${NC} http://localhost:$SERVICE_PORT/health"
echo -e "${BLUE}Capabilities:${NC} http://localhost:$SERVICE_PORT/capabilities"
echo ""
echo -e "${BLUE}Management Commands:${NC}"
echo -e "  ${YELLOW}View logs:${NC} docker logs $CONTAINER_NAME"
echo -e "  ${YELLOW}Stop service:${NC} docker-compose down"
echo -e "  ${YELLOW}Restart service:${NC} docker-compose restart"
echo -e "  ${YELLOW}Service status:${NC} docker-compose ps"
echo ""
echo -e "${BLUE}The service is now ready to accept LangChain workflow requests!${NC}"