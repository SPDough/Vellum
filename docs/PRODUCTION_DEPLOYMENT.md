# Production Deployment with CI/CD

This guide covers setting up automated production deployment for the Otomeshon application using GitHub Actions.

## Overview

The CI/CD pipeline automatically:
1. Runs tests and security scans
2. Builds Docker images
3. Pushes images to GitHub Container Registry
4. Deploys to production when code is merged to `main` branch

## Prerequisites

### 1. Production Server Setup

Your production server should have:
- Ubuntu 20.04+ or RHEL 8+
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM, 50GB storage
- Static IP address

### 2. Domain and SSL Setup

- Register a domain name
- Point DNS to your production server
- Set up SSL certificates (Let's Encrypt recommended)

### 3. GitHub Repository Secrets

Configure these secrets in your GitHub repository (`Settings > Secrets and variables > Actions`):

#### Required Secrets:
- `DEPLOY_HOST`: Your production server IP or domain
- `DEPLOY_USER`: SSH username for production server
- `DEPLOY_SSH_KEY`: Private SSH key for server access
- `DEPLOY_PATH`: Path to application on production server (e.g., `/opt/otomeshon`)

#### Optional Secrets:
- `SLACK_WEBHOOK_URL`: For deployment notifications
- `SLACK_NOTIFICATIONS_ENABLED`: Set to `true` to enable Slack notifications

## Setup Steps

### 1. Prepare Production Server

```bash
# On your production server
sudo apt update
sudo apt install docker.io docker-compose curl

# Create application directory
sudo mkdir -p /opt/otomeshon
sudo chown $USER:$USER /opt/otomeshon
cd /opt/otomeshon

# Clone the repository
git clone https://github.com/your-username/Vellum.git .
```

### 2. Configure Environment Variables

Create `.env` file on production server:

```bash
# Core Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=false
LOG_LEVEL=info

# Database
POSTGRES_PASSWORD=your-secure-postgres-password
DATABASE_URL=postgresql://otomeshon:${POSTGRES_PASSWORD}@postgres:5432/otomeshon

# Redis
REDIS_PASSWORD=your-redis-password

# Neo4j
NEO4J_PASSWORD=your-neo4j-password

# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Security
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Domain
DOMAIN=your-domain.com
ADMIN_EMAIL=admin@your-domain.com
```

### 3. Setup SSH Access

Generate SSH key pair for deployment:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-deploy

# Copy public key to production server
ssh-copy-id -i ~/.ssh/github-deploy.pub user@your-production-server

# Add private key to GitHub secrets
cat ~/.ssh/github-deploy
# Copy the output and add as DEPLOY_SSH_KEY secret
```

### 4. Configure GitHub Secrets

In your GitHub repository, go to `Settings > Secrets and variables > Actions` and add:

| Secret Name | Value |
|-------------|-------|
| `DEPLOY_HOST` | Your production server IP or domain |
| `DEPLOY_USER` | SSH username for production server |
| `DEPLOY_SSH_KEY` | Private SSH key content |
| `DEPLOY_PATH` | `/opt/otomeshon` |

### 5. Setup SSL Certificates

```bash
# On production server
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Create SSL directory
mkdir -p /opt/otomeshon/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/otomeshon/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/otomeshon/ssl/
sudo chown $USER:$USER /opt/otomeshon/ssl/*
```

### 6. Initial Deployment

```bash
# On production server
cd /opt/otomeshon

# Pull and start services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

## CI/CD Pipeline

### Automatic Deployment

The pipeline automatically deploys when:
- Code is pushed to `main` branch
- All tests pass
- Security scans pass
- Docker images build successfully

### Manual Deployment

To trigger deployment manually:

1. Go to your GitHub repository
2. Navigate to `Actions` tab
3. Select `CI/CD Pipeline` workflow
4. Click `Run workflow`
5. Select `main` branch
6. Click `Run workflow`

### Deployment Process

1. **Build Phase**: Builds Docker images for frontend and backend
2. **Push Phase**: Pushes images to GitHub Container Registry
3. **Deploy Phase**: 
   - Connects to production server via SSH
   - Pulls latest images
   - Runs database migrations
   - Starts services with health checks
   - Verifies deployment

## Monitoring and Maintenance

### Health Checks

The deployment includes automatic health checks:
- Backend API health endpoint
- Frontend accessibility
- Database connectivity

### Logs

View deployment logs:
```bash
# On production server
docker-compose -f docker-compose.prod.yml logs -f
```

### Backup

Automatic backups are created before each deployment:
```bash
# View backups
ls -la /opt/otomeshon/backups/
```

### Rollback

To rollback to previous version:
```bash
# On production server
cd /opt/otomeshon

# Stop current services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
docker-compose -f docker-compose.prod.yml up -d postgres
docker-compose -f docker-compose.prod.yml exec postgres psql -U otomeshon -d otomeshon < backups/otomeshon-backup-YYYYMMDD-HHMMSS-postgres.sql

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Verify SSH key is correct
   - Check server firewall settings
   - Ensure user has sudo access

2. **Docker Images Not Found**
   - Check GitHub Container Registry permissions
   - Verify image names in docker-compose.prod.yml

3. **Health Checks Fail**
   - Check service logs: `docker-compose -f docker-compose.prod.yml logs service-name`
   - Verify environment variables
   - Check port availability

4. **Database Migration Errors**
   - Check database connectivity
   - Verify database credentials
   - Review migration files

### Debugging

Enable debug mode in production:
```bash
# Edit .env file
DEBUG=true
LOG_LEVEL=debug

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

## Security Considerations

1. **Secrets Management**: Never commit secrets to repository
2. **SSL/TLS**: Always use HTTPS in production
3. **Firewall**: Configure firewall to allow only necessary ports
4. **Updates**: Regularly update dependencies and base images
5. **Monitoring**: Set up monitoring and alerting

## Performance Optimization

1. **Resource Limits**: Set appropriate Docker resource limits
2. **Caching**: Configure Redis for optimal caching
3. **Database**: Optimize PostgreSQL configuration
4. **CDN**: Consider using a CDN for static assets

## Support

For deployment issues:
1. Check GitHub Actions logs
2. Review production server logs
3. Verify environment configuration
4. Test connectivity manually
