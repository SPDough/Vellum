#!/bin/bash

# Otomeshon Production Deployment Script
# This script deploys the Otomeshon application to production

set -e

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/opt/otomeshon/backups"
LOG_FILE="/var/log/otomeshon-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Check if Docker and Docker Compose are installed
command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is required but not installed"

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    error ".env file not found. Please create one based on .env.example"
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting Otomeshon production deployment..."

# Pre-deployment checks
log "Running pre-deployment checks..."

# Check disk space (require at least 5GB free)
AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
REQUIRED_SPACE=5242880  # 5GB in KB
if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
    error "Insufficient disk space. At least 5GB required."
fi

# Create backup of current deployment if it exists
if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
    log "Creating backup of current deployment..."
    BACKUP_NAME="otomeshon-backup-$(date +%Y%m%d-%H%M%S)"
    
    # Backup database
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_dump -U otomeshon otomeshon > "$BACKUP_DIR/$BACKUP_NAME-postgres.sql" || warning "Database backup failed"
    
    # Backup Redis data
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli --rdb - > "$BACKUP_DIR/$BACKUP_NAME-redis.rdb" || warning "Redis backup failed"
    
    log "Backup completed: $BACKUP_NAME"
fi

# Pull latest images
log "Pulling latest Docker images..."
docker-compose -f "$DOCKER_COMPOSE_FILE" pull

# Run database migrations if needed
log "Running database migrations..."
docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend alembic upgrade head || warning "Database migration failed"

# Start services with rolling update
log "Starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans

# Wait for services to be healthy
log "Waiting for services to be healthy..."
TIMEOUT=300  # 5 minutes
COUNTER=0

while [[ $COUNTER -lt $TIMEOUT ]]; do
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "unhealthy\|starting"; then
        sleep 5
        COUNTER=$((COUNTER + 5))
        echo -n "."
    else
        break
    fi
done

if [[ $COUNTER -ge $TIMEOUT ]]; then
    error "Services failed to start within timeout period"
fi

echo ""
log "Services are healthy!"

# Run health checks
log "Running post-deployment health checks..."

# Check backend health
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [[ "$BACKEND_HEALTH" != "200" ]]; then
    error "Backend health check failed (HTTP $BACKEND_HEALTH)"
fi

# Check frontend
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost || echo "000")
if [[ "$FRONTEND_HEALTH" != "200" ]]; then
    error "Frontend health check failed (HTTP $FRONTEND_HEALTH)"
fi

# Check database connectivity
DB_CHECK=$(docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U otomeshon || echo "failed")
if [[ "$DB_CHECK" == *"failed"* ]]; then
    error "Database connectivity check failed"
fi

# Cleanup old images and containers
log "Cleaning up old Docker resources..."
docker system prune -f --volumes || warning "Docker cleanup failed"

# Clean up old backups (keep last 7 days)
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "otomeshon-backup-*" -mtime +7 -delete || warning "Backup cleanup failed"

log "Deployment completed successfully!"
log "Application is available at: http://$(hostname -I | awk '{print $1}')"
log "Monitoring is available at: http://$(hostname -I | awk '{print $1}'):3001"

# Display running services
echo ""
log "Running services:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

echo ""
log "Deployment log saved to: $LOG_FILE"
log "🚀 Otomeshon is now running in production!"