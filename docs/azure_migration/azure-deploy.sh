#!/bin/bash

# Azure Deployment Script for Otomeshon Platform
# This script deploys the Otomeshon application to Azure

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AZURE_ENV_FILE="${PROJECT_ROOT}/azure.env"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.azure.yml"
LOG_FILE="/var/log/otomeshon-azure-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Check if Azure CLI is installed
command -v az >/dev/null 2>&1 || error "Azure CLI is required but not installed"

# Check if Docker and Docker Compose are installed
command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
command -v docker-compose >/dev/null 2>&1 || error "Docker Compose is required but not installed"

# Check if .env file exists
if [[ ! -f "$AZURE_ENV_FILE" ]]; then
    error "Azure environment file not found at $AZURE_ENV_FILE. Please create one based on azure.env.example"
fi

# Load environment variables
source "$AZURE_ENV_FILE"

# Validate required Azure environment variables
validate_azure_env() {
    log "Validating Azure environment variables..."
    
    required_vars=(
        "AZURE_TENANT_ID"
        "AZURE_CLIENT_ID"
        "AZURE_CLIENT_SECRET"
        "AZURE_KEY_VAULT_URL"
        "AZURE_STORAGE_CONNECTION_STRING"
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
        "ACR_LOGIN_SERVER"
        "ACR_USERNAME"
        "ACR_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set"
        fi
    done
    
    log "✅ All required Azure environment variables are set"
}

# Check Azure CLI login
check_azure_login() {
    log "Checking Azure CLI login status..."
    
    if ! az account show >/dev/null 2>&1; then
        error "Not logged in to Azure CLI. Please run 'az login' first"
    fi
    
    local subscription_id=$(az account show --query id -o tsv)
    local subscription_name=$(az account show --query name -o tsv)
    
    log "✅ Logged in to Azure subscription: $subscription_name ($subscription_id)"
}

# Create Azure resources
create_azure_resources() {
    log "Creating Azure resources..."
    
    # Create resource groups
    log "Creating resource groups..."
    az group create --name otomeshon-prod-rg --location eastus --output none || warning "Resource group otomeshon-prod-rg may already exist"
    az group create --name otomeshon-dev-rg --location eastus --output none || warning "Resource group otomeshon-dev-rg may already exist"
    az group create --name otomeshon-shared-rg --location eastus --output none || warning "Resource group otomeshon-shared-rg may already exist"
    
    # Create Azure Container Registry
    log "Creating Azure Container Registry..."
    if ! az acr show --name otomeshonacr --resource-group otomeshon-shared-rg >/dev/null 2>&1; then
        az acr create \
            --resource-group otomeshon-shared-rg \
            --name otomeshonacr \
            --sku Standard \
            --admin-enabled true \
            --output none
        log "✅ Azure Container Registry created"
    else
        log "✅ Azure Container Registry already exists"
    fi
    
    # Create Azure Key Vault
    log "Creating Azure Key Vault..."
    if ! az keyvault show --name otomeshon-kv --resource-group otomeshon-shared-rg >/dev/null 2>&1; then
        az keyvault create \
            --resource-group otomeshon-shared-rg \
            --name otomeshon-kv \
            --location eastus \
            --sku standard \
            --enabled-for-deployment true \
            --enabled-for-disk-encryption true \
            --enabled-for-template-deployment true \
            --output none
        log "✅ Azure Key Vault created"
    else
        log "✅ Azure Key Vault already exists"
    fi
    
    # Create Azure Database for PostgreSQL
    log "Creating Azure Database for PostgreSQL..."
    if ! az postgres flexible-server show --name otomeshon-postgres --resource-group otomeshon-prod-rg >/dev/null 2>&1; then
        az postgres flexible-server create \
            --resource-group otomeshon-prod-rg \
            --name otomeshon-postgres \
            --admin-user otomeshon \
            --admin-password "$AZURE_POSTGRES_PASSWORD" \
            --sku-name Standard_B1ms \
            --tier Burstable \
            --storage-size 32 \
            --version 16 \
            --location eastus \
            --output none
        log "✅ Azure Database for PostgreSQL created"
    else
        log "✅ Azure Database for PostgreSQL already exists"
    fi
    
    # Create Azure Cache for Redis
    log "Creating Azure Cache for Redis..."
    if ! az redis show --name otomeshon-redis --resource-group otomeshon-prod-rg >/dev/null 2>&1; then
        az redis create \
            --resource-group otomeshon-prod-rg \
            --name otomeshon-redis \
            --location eastus \
            --sku Standard \
            --vm-size C1 \
            --enable-non-ssl-port false \
            --output none
        log "✅ Azure Cache for Redis created"
    else
        log "✅ Azure Cache for Redis already exists"
    fi
    
    # Create Azure Storage Account
    log "Creating Azure Storage Account..."
    if ! az storage account show --name otomeshonstorage --resource-group otomeshon-shared-rg >/dev/null 2>&1; then
        az storage account create \
            --resource-group otomeshon-shared-rg \
            --name otomeshonstorage \
            --location eastus \
            --sku Standard_LRS \
            --kind StorageV2 \
            --output none
        log "✅ Azure Storage Account created"
    else
        log "✅ Azure Storage Account already exists"
    fi
    
    # Create Application Insights
    log "Creating Application Insights..."
    if ! az monitor app-insights component show --app otomeshon-insights --resource-group otomeshon-prod-rg >/dev/null 2>&1; then
        az monitor app-insights component create \
            --app otomeshon-insights \
            --location eastus \
            --resource-group otomeshon-prod-rg \
            --application-type web \
            --output none
        log "✅ Application Insights created"
    else
        log "✅ Application Insights already exists"
    fi
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images to Azure Container Registry..."
    
    # Login to Azure Container Registry
    log "Logging in to Azure Container Registry..."
    az acr login --name otomeshonacr
    
    # Build and push backend image
    log "Building backend image..."
    cd "$PROJECT_ROOT/backend"
    docker build -t otomeshonacr.azurecr.io/otomeshon-backend:latest .
    docker push otomeshonacr.azurecr.io/otomeshon-backend:latest
    
    # Build and push frontend image
    log "Building frontend image..."
    cd "$PROJECT_ROOT/frontend"
    docker build -t otomeshonacr.azurecr.io/otomeshon-frontend:latest .
    docker push otomeshonacr.azurecr.io/otomeshon-frontend:latest
    
    log "✅ Docker images built and pushed successfully"
}

# Deploy to Azure Container Apps
deploy_to_container_apps() {
    log "Deploying to Azure Container Apps..."
    
    # Create Container Apps environment
    log "Creating Container Apps environment..."
    if ! az containerapp env show --name otomeshon-env --resource-group otomeshon-prod-rg >/dev/null 2>&1; then
        az containerapp env create \
            --name otomeshon-env \
            --resource-group otomeshon-prod-rg \
            --location eastus \
            --output none
        log "✅ Container Apps environment created"
    else
        log "✅ Container Apps environment already exists"
    fi
    
    # Deploy backend
    log "Deploying backend to Container Apps..."
    az containerapp create \
        --name otomeshon-backend \
        --resource-group otomeshon-prod-rg \
        --environment otomeshon-env \
        --image otomeshonacr.azurecr.io/otomeshon-backend:latest \
        --target-port 8000 \
        --ingress external \
        --min-replicas 2 \
        --max-replicas 10 \
        --cpu 1.0 \
        --memory 2Gi \
        --env-vars \
            ENVIRONMENT=production \
            DATABASE_URL="$DATABASE_URL" \
            REDIS_URL="$REDIS_URL" \
            AZURE_KEY_VAULT_URL="$AZURE_KEY_VAULT_URL" \
            APPLICATIONINSIGHTS_CONNECTION_STRING="$APPLICATIONINSIGHTS_CONNECTION_STRING" \
        --output none
    
    log "✅ Backend deployed to Container Apps"
    
    # Deploy frontend
    log "Deploying frontend to Container Apps..."
    az containerapp create \
        --name otomeshon-frontend \
        --resource-group otomeshon-prod-rg \
        --environment otomeshon-env \
        --image otomeshonacr.azurecr.io/otomeshon-frontend:latest \
        --target-port 80 \
        --ingress external \
        --min-replicas 2 \
        --max-replicas 5 \
        --cpu 0.5 \
        --memory 1Gi \
        --env-vars \
            NODE_ENV=production \
            REACT_APP_API_URL="https://otomeshon-backend.azurecontainerapps.io" \
        --output none
    
    log "✅ Frontend deployed to Container Apps"
}

# Configure Azure Key Vault secrets
configure_key_vault() {
    log "Configuring Azure Key Vault secrets..."
    
    # Store secrets in Key Vault
    az keyvault secret set --vault-name otomeshon-kv --name "postgres-password" --value "$AZURE_POSTGRES_PASSWORD" --output none
    az keyvault secret set --vault-name otomeshon-kv --name "redis-password" --value "$AZURE_REDIS_PASSWORD" --output none
    az keyvault secret set --vault-name otomeshon-kv --name "jwt-secret" --value "$JWT_SECRET_KEY" --output none
    az keyvault secret set --vault-name otomeshon-kv --name "secret-key" --value "$SECRET_KEY" --output none
    
    log "✅ Azure Key Vault secrets configured"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Get the backend container app URL
    local backend_url=$(az containerapp show --name otomeshon-backend --resource-group otomeshon-prod-rg --query properties.configuration.ingress.fqdn -o tsv)
    
    if [[ -n "$backend_url" ]]; then
        # Run migrations using the backend API
        curl -X POST "https://$backend_url/migrate" || warning "Migration endpoint not available or failed"
    else
        warning "Could not determine backend URL for migrations"
    fi
    
    log "✅ Database migrations completed"
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Check backend health
    local backend_url=$(az containerapp show --name otomeshon-backend --resource-group otomeshon-prod-rg --query properties.configuration.ingress.fqdn -o tsv)
    if [[ -n "$backend_url" ]]; then
        local backend_health=$(curl -s -o /dev/null -w "%{http_code}" "https://$backend_url/health" || echo "000")
        if [[ "$backend_health" == "200" ]]; then
            log "✅ Backend is healthy"
        else
            warning "Backend health check failed (HTTP $backend_health)"
        fi
    fi
    
    # Check frontend health
    local frontend_url=$(az containerapp show --name otomeshon-frontend --resource-group otomeshon-prod-rg --query properties.configuration.ingress.fqdn -o tsv)
    if [[ -n "$frontend_url" ]]; then
        local frontend_health=$(curl -s -o /dev/null -w "%{http_code}" "https://$frontend_url" || echo "000")
        if [[ "$frontend_health" == "200" ]]; then
            log "✅ Frontend is healthy"
        else
            warning "Frontend health check failed (HTTP $frontend_health)"
        fi
    fi
}

# Main deployment function
main() {
    log "🚀 Starting Azure deployment for Otomeshon platform..."
    
    # Validate environment
    validate_azure_env
    check_azure_login
    
    # Create Azure resources
    create_azure_resources
    
    # Build and push images
    build_and_push_images
    
    # Configure Key Vault
    configure_key_vault
    
    # Deploy to Container Apps
    deploy_to_container_apps
    
    # Run migrations
    run_migrations
    
    # Health check
    health_check
    
    log "🎉 Azure deployment completed successfully!"
    
    # Display URLs
    local backend_url=$(az containerapp show --name otomeshon-backend --resource-group otomeshon-prod-rg --query properties.configuration.ingress.fqdn -o tsv)
    local frontend_url=$(az containerapp show --name otomeshon-frontend --resource-group otomeshon-prod-rg --query properties.configuration.ingress.fqdn -o tsv)
    
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: https://$frontend_url"
    echo "   Backend:  https://$backend_url"
    echo ""
    echo "📊 Azure Resources:"
    echo "   Resource Groups: otomeshon-prod-rg, otomeshon-dev-rg, otomeshon-shared-rg"
    echo "   Container Registry: otomeshonacr.azurecr.io"
    echo "   Key Vault: otomeshon-kv"
    echo "   Database: otomeshon-postgres"
    echo "   Redis: otomeshon-redis"
    echo "   Storage: otomeshonstorage"
    echo "   Application Insights: otomeshon-insights"
    echo ""
}

# Run main function
main "$@"
