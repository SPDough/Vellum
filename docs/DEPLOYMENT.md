# Otomeshon Production Deployment Guide

This guide covers deploying the Otomeshon application to production using Docker containers and comprehensive monitoring.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or RHEL 8+ (recommended)
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: Minimum 50GB SSD
- **CPU**: 4+ cores recommended
- **Network**: Static IP address and domain name

### Required Software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- curl
- SSL certificates (Let's Encrypt recommended)

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd Otomeshon_1.0
   cp .env.example .env
   ```

2. **Configure Environment**
   Edit `.env` file with your production values:
   ```bash
   # Required: Change these values
   SECRET_KEY=your-super-secret-key-here
   POSTGRES_PASSWORD=your-secure-postgres-password
   REDIS_PASSWORD=your-redis-password
   NEO4J_PASSWORD=your-neo4j-password
   GRAFANA_PASSWORD=your-grafana-password
   DOMAIN=your-domain.com
   ADMIN_EMAIL=admin@your-domain.com
   
   # API Keys
   OPENAI_API_KEY=sk-your-openai-key
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
   ```

3. **Deploy**
   ```bash
   ./scripts/deploy.sh
   ```

## Detailed Deployment Steps

### 1. Environment Configuration

#### Core Application Settings
```env
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=false
LOG_LEVEL=info
```

#### Database Configuration
```env
POSTGRES_PASSWORD=your-postgres-password
DATABASE_URL=postgresql://otomeshon:${POSTGRES_PASSWORD}@postgres:5432/otomeshon
```

#### Security Settings
```env
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 2. SSL Certificate Setup

#### Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./certs/
sudo chown $(whoami):$(whoami) ./certs/*
```

### 3. Docker Deployment

#### Start All Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Verify Deployment
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 4. Database Setup

#### Initialize Database
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create admin user (optional)
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py
```

### 5. Monitoring Setup

Access monitoring dashboards:
- **Grafana**: http://your-domain.com:3001
  - Username: admin
  - Password: (from GRAFANA_PASSWORD in .env)
- **Prometheus**: http://your-domain.com:9090

## Service URLs

Once deployed, your services will be available at:

- **Frontend**: https://your-domain.com
- **Backend API**: https://your-domain.com/api
- **API Documentation**: https://your-domain.com/docs
- **Grafana Monitoring**: https://your-domain.com:3001
- **Prometheus**: https://your-domain.com:9090 (internal)

## Health Checks

### Manual Health Checks
```bash
# Backend API health
curl https://your-domain.com/api/health

# Frontend
curl https://your-domain.com

# Database connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U otomeshon
```

### Automated Monitoring
The deployment includes comprehensive monitoring with:
- **System metrics**: CPU, memory, disk, network
- **Application metrics**: Request rates, response times, errors
- **Database metrics**: Connection pools, query performance
- **Custom metrics**: WebSocket connections, data sandbox usage

## Backup and Recovery

### Automated Backups
Backups are configured to run daily at 2 AM:
```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U otomeshon otomeshon > backup.sql

# Manual Redis backup
docker-compose -f docker-compose.prod.yml exec redis redis-cli --rdb backup.rdb
```

### Recovery
```bash
# Restore PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U otomeshon otomeshon < backup.sql

# Restore Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli --pipe < backup.rdb
```

## Scaling and Performance

### Horizontal Scaling
To scale services:
```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale frontend instances
docker-compose -f docker-compose.prod.yml up -d --scale frontend=2
```

### Performance Tuning
Key configuration files for performance:
- `nginx/nginx.conf`: Frontend and reverse proxy settings
- `backend/gunicorn.conf.py`: Backend worker configuration
- `docker-compose.prod.yml`: Resource limits and reservations

## Security

### Firewall Configuration
```bash
# Allow essential ports only
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Security Best Practices
- Use strong passwords for all services
- Regularly update Docker images
- Monitor security logs
- Enable automatic security updates
- Use secrets management for API keys

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check resource usage
docker stats

# Check disk space
df -h
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.database import get_db
print('Database connection successful')
"
```

#### SSL Certificate Issues
```bash
# Verify certificate
openssl x509 -in ./certs/fullchain.pem -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443
```

### Log Locations
- Application logs: `/var/log/otomeshon/`
- Deployment logs: `/var/log/otomeshon-deploy.log`
- Container logs: `docker-compose logs`

## Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check monitoring dashboards
2. **Monthly**: Update Docker images
3. **Quarterly**: Review and rotate secrets
4. **As needed**: Scale resources based on usage

### Updates
```bash
# Pull latest code
git pull origin main

# Update and restart services
./scripts/deploy.sh
```

## Support

For issues and support:
1. Check monitoring dashboards for alerts
2. Review application logs
3. Consult troubleshooting section
4. Contact development team

## Architecture Overview

The production deployment includes:
- **Load Balancer**: Nginx reverse proxy
- **Frontend**: React application served by Nginx
- **Backend**: FastAPI with Gunicorn workers
- **Databases**: PostgreSQL, Redis, Neo4j
- **Message Queue**: Apache Kafka
- **Monitoring**: Prometheus + Grafana
- **Search**: Elasticsearch (optional)
- **Workflow Engine**: Temporal (optional)

All services run in Docker containers with proper resource limits, health checks, and restart policies.