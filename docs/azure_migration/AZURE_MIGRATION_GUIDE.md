# Azure Migration Guide for Otomeshon Platform

This guide provides a comprehensive approach to migrating the Otomeshon banking platform to Azure for production deployment.

## Table of Contents

1. [Overview](#overview)
2. [Azure Services Mapping](#azure-services-mapping)
3. [Prerequisites](#prerequisites)
4. [Migration Strategy](#migration-strategy)
5. [Azure Infrastructure Setup](#azure-infrastructure-setup)
6. [Configuration Changes](#configuration-changes)
7. [Deployment Options](#deployment-options)
8. [Security & Compliance](#security--compliance)
9. [Monitoring & Observability](#monitoring--observability)
10. [Cost Optimization](#cost-optimization)
11. [Migration Checklist](#migration-checklist)
12. [Troubleshooting](#troubleshooting)

## Overview

The Otomeshon platform is designed as a microservices architecture with the following key components:

- **Backend**: FastAPI with Python 3.12
- **Frontend**: React 18 with TypeScript
- **Databases**: PostgreSQL (with pgvector), Neo4j, Redis
- **Message Queue**: Apache Kafka
- **Workflow Engine**: Temporal
- **Authentication**: Keycloak
- **Monitoring**: Prometheus + Grafana + Jaeger
- **AI/ML**: LangChain, LangGraph, Ollama

## Azure Services Mapping

| Current Component | Azure Service | Alternative Options |
|------------------|---------------|-------------------|
| **Application Hosting** | Azure Container Apps | Azure Kubernetes Service (AKS), Azure App Service |
| **PostgreSQL Database** | Azure Database for PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| **Neo4j Graph Database** | Azure Cosmos DB (Gremlin API) | Self-hosted Neo4j on Azure VM |
| **Redis Cache** | Azure Cache for Redis | Self-hosted Redis on Azure VM |
| **Message Queue** | Azure Service Bus | Azure Event Hubs, Apache Kafka on HDInsight |
| **File Storage** | Azure Blob Storage | Azure Files |
| **Secrets Management** | Azure Key Vault | HashiCorp Vault |
| **Monitoring** | Azure Monitor | Application Insights, Log Analytics |
| **Load Balancer** | Azure Application Gateway | Azure Load Balancer |
| **CDN** | Azure CDN | Azure Front Door |
| **DNS** | Azure DNS | External DNS provider |

## Prerequisites

### Azure Account Setup

1. **Azure Subscription**
   - Create or use existing Azure subscription
   - Ensure sufficient quota for required resources
   - Set up billing alerts

2. **Azure CLI Installation**
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Login to Azure
   az login
   
   # Set subscription
   az account set --subscription "your-subscription-id"
   ```

3. **Required Azure Providers**
   ```bash
   # Register required providers
   az provider register --namespace Microsoft.ContainerService
   az provider register --namespace Microsoft.OperationalInsights
   az provider register --namespace Microsoft.OperationsManagement
   az provider register --namespace Microsoft.OperationalInsights
   az provider register --namespace Microsoft.Insights
   ```

### Development Environment

1. **Docker Desktop** with Azure integration
2. **Azure Storage Explorer**
3. **Azure Data Studio** (for database management)
4. **Visual Studio Code** with Azure extensions

## Migration Strategy

### Phase 1: Infrastructure Preparation (Week 1-2)

1. **Azure Resource Group Setup**
   - Create resource groups for different environments
   - Set up networking (VNet, subnets, NSGs)
   - Configure Azure Key Vault

2. **Database Migration Planning**
   - Plan PostgreSQL migration strategy
   - Design Neo4j migration approach
   - Set up Azure Cache for Redis

3. **Storage Setup**
   - Configure Azure Blob Storage
   - Set up Azure Files for shared storage
   - Configure backup storage

### Phase 2: Application Migration (Week 3-4)

1. **Container Registry Setup**
   - Create Azure Container Registry (ACR)
   - Configure image builds and pushes
   - Set up automated builds

2. **Application Configuration**
   - Update configuration for Azure services
   - Implement Azure Key Vault integration
   - Configure Azure Monitor

3. **Database Migration**
   - Migrate PostgreSQL data
   - Migrate Neo4j data
   - Test data integrity

### Phase 3: Deployment & Testing (Week 5-6)

1. **Deployment Pipeline**
   - Set up Azure DevOps or GitHub Actions
   - Configure CI/CD pipelines
   - Implement blue-green deployment

2. **Testing & Validation**
   - Performance testing
   - Security testing
   - Compliance validation

3. **Go-Live Preparation**
   - Final testing
   - Documentation
   - Rollback procedures

## Azure Infrastructure Setup

### 1. Resource Groups

```bash
# Create resource groups
az group create --name otomeshon-prod-rg --location eastus
az group create --name otomeshon-dev-rg --location eastus
az group create --name otomeshon-shared-rg --location eastus
```

### 2. Virtual Network

```bash
# Create VNet
az network vnet create \
  --resource-group otomeshon-prod-rg \
  --name otomeshon-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name default \
  --subnet-prefix 10.0.1.0/24

# Create subnets
az network vnet subnet create \
  --resource-group otomeshon-prod-rg \
  --vnet-name otomeshon-vnet \
  --name app-subnet \
  --address-prefix 10.0.2.0/24

az network vnet subnet create \
  --resource-group otomeshon-prod-rg \
  --vnet-name otomeshon-vnet \
  --name db-subnet \
  --address-prefix 10.0.3.0/24
```

### 3. Azure Container Registry

```bash
# Create ACR
az acr create \
  --resource-group otomeshon-shared-rg \
  --name otomeshonacr \
  --sku Standard \
  --admin-enabled true

# Get ACR credentials
az acr credential show --name otomeshonacr
```

### 4. Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group otomeshon-prod-rg \
  --name otomeshon-postgres \
  --admin-user otomeshon \
  --admin-password "SecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 16 \
  --location eastus \
  --subnet /subscriptions/your-sub-id/resourceGroups/otomeshon-prod-rg/providers/Microsoft.Network/virtualNetworks/otomeshon-vnet/subnets/db-subnet

# Enable pgvector extension
az postgres flexible-server parameter set \
  --resource-group otomeshon-prod-rg \
  --server-name otomeshon-postgres \
  --name shared_preload_libraries \
  --value "vector"
```

### 5. Azure Cache for Redis

```bash
# Create Redis cache
az redis create \
  --resource-group otomeshon-prod-rg \
  --name otomeshon-redis \
  --location eastus \
  --sku Standard \
  --vm-size C1 \
  --enable-non-ssl-port false
```

### 6. Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --resource-group otomeshon-shared-rg \
  --name otomeshon-kv \
  --location eastus \
  --sku standard \
  --enabled-for-deployment true \
  --enabled-for-disk-encryption true \
  --enabled-for-template-deployment true

# Store secrets
az keyvault secret set --vault-name otomeshon-kv --name "postgres-password" --value "SecurePassword123!"
az keyvault secret set --vault-name otomeshon-kv --name "redis-password" --value "SecureRedisPassword123!"
az keyvault secret set --vault-name otomeshon-kv --name "jwt-secret" --value "your-jwt-secret-key"
```

## Configuration Changes

### 1. Environment Variables

Create `azure.env` file:

```env
# Azure Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Database URLs
DATABASE_URL=postgresql://otomeshon:${POSTGRES_PASSWORD}@otomeshon-postgres.postgres.database.azure.com:5432/otomeshon?sslmode=require
REDIS_URL=rediss://otomeshon-redis.redis.cache.windows.net:6380/0?ssl=true&password=${REDIS_PASSWORD}

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string
AZURE_STORAGE_ACCOUNT_NAME=otomeshonstorage
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key

# Azure Key Vault
AZURE_KEY_VAULT_URL=https://otomeshon-kv.vault.azure.net/
AZURE_KEY_VAULT_TENANT_ID=your-tenant-id
AZURE_KEY_VAULT_CLIENT_ID=your-client-id
AZURE_KEY_VAULT_CLIENT_SECRET=your-client-secret

# Azure Monitor
APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights-connection-string
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=your-instrumentation-key

# Azure Container Registry
ACR_LOGIN_SERVER=otomeshonacr.azurecr.io
ACR_USERNAME=otomeshonacr
ACR_PASSWORD=your-acr-password
```

### 2. Updated Docker Compose for Azure

Create `docker-compose.azure.yml`:

```yaml
version: '3.8'

services:
  # Frontend - Azure Container Apps
  frontend:
    image: ${ACR_LOGIN_SERVER}/otomeshon-frontend:latest
    environment:
      - REACT_APP_API_URL=https://otomeshon-api.azurewebsites.net
      - REACT_APP_KEYCLOAK_URL=https://otomeshon-keycloak.azurewebsites.net
      - NODE_ENV=production
    ports:
      - "80:80"
      - "443:443"

  # Backend - Azure Container Apps
  backend:
    image: ${ACR_LOGIN_SERVER}/otomeshon-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING}
      - AZURE_KEY_VAULT_URL=${AZURE_KEY_VAULT_URL}
      - APPLICATIONINSIGHTS_CONNECTION_STRING=${APPLICATIONINSIGHTS_CONNECTION_STRING}
      - ENVIRONMENT=production
    ports:
      - "8000:8000"

  # Azure Database for PostgreSQL (external)
  # Managed by Azure - no container needed

  # Azure Cache for Redis (external)
  # Managed by Azure - no container needed
```

### 3. Azure Container Apps Configuration

Create `container-apps.yaml`:

```yaml
apiVersion: 2023-05-01
location: eastus
name: otomeshon-backend
properties:
  managedEnvironmentId: /subscriptions/your-sub-id/resourceGroups/otomeshon-prod-rg/providers/Microsoft.App/managedEnvironments/otomeshon-env
  configuration:
    ingress:
      external: true
      targetPort: 8000
      traffic:
        - latestRevision: true
          weight: 100
    secrets:
      - name: postgres-password
        keyVaultUrl: https://otomeshon-kv.vault.azure.net/secrets/postgres-password
      - name: redis-password
        keyVaultUrl: https://otomeshon-kv.vault.azure.net/secrets/redis-password
  template:
    containers:
      - name: backend
        image: otomeshonacr.azurecr.io/otomeshon-backend:latest
        resources:
          cpu: 1.0
          memory: 2Gi
        env:
          - name: DATABASE_URL
            secretRef: postgres-password
          - name: REDIS_URL
            secretRef: redis-password
          - name: ENVIRONMENT
            value: production
    scale:
      minReplicas: 2
      maxReplicas: 10
      rules:
        - name: http-rule
          http:
            metadata:
              concurrentRequests: 100
```

## Deployment Options

### Option 1: Azure Container Apps (Recommended)

**Pros:**
- Serverless container platform
- Automatic scaling
- Built-in monitoring
- Cost-effective for variable workloads

**Cons:**
- Limited customization
- Newer service with evolving features

**Setup:**
```bash
# Create Container Apps environment
az containerapp env create \
  --name otomeshon-env \
  --resource-group otomeshon-prod-rg \
  --location eastus

# Deploy backend
az containerapp create \
  --name otomeshon-backend \
  --resource-group otomeshon-prod-rg \
  --environment otomeshon-env \
  --image otomeshonacr.azurecr.io/otomeshon-backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 2 \
  --max-replicas 10
```

### Option 2: Azure Kubernetes Service (AKS)

**Pros:**
- Full Kubernetes control
- Advanced orchestration features
- Mature ecosystem

**Cons:**
- Higher complexity
- More expensive
- Requires Kubernetes expertise

**Setup:**
```bash
# Create AKS cluster
az aks create \
  --resource-group otomeshon-prod-rg \
  --name otomeshon-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --network-plugin azure \
  --network-policy azure

# Get credentials
az aks get-credentials --resource-group otomeshon-prod-rg --name otomeshon-aks
```

### Option 3: Azure App Service

**Pros:**
- Simple deployment
- Built-in CI/CD
- Cost-effective for smaller applications

**Cons:**
- Limited container support
- Less flexible scaling

## Security & Compliance

### 1. Network Security

```bash
# Create Network Security Groups
az network nsg create \
  --resource-group otomeshon-prod-rg \
  --name otomeshon-nsg

# Add security rules
az network nsg rule create \
  --resource-group otomeshon-prod-rg \
  --nsg-name otomeshon-nsg \
  --name allow-https \
  --protocol tcp \
  --priority 100 \
  --destination-port-range 443

az network nsg rule create \
  --resource-group otomeshon-prod-rg \
  --nsg-name otomeshon-nsg \
  --name allow-http \
  --protocol tcp \
  --priority 200 \
  --destination-port-range 80
```

### 2. Azure Key Vault Integration

```python
# backend/app/core/azure_key_vault.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class AzureKeyVault:
    def __init__(self, vault_url: str):
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=self.credential)
    
    def get_secret(self, secret_name: str) -> str:
        return self.client.get_secret(secret_name).value
```

### 3. Managed Identity

```bash
# Enable managed identity for Container Apps
az containerapp identity assign \
  --name otomeshon-backend \
  --resource-group otomeshon-prod-rg \
  --system-assigned

# Grant Key Vault access
az keyvault set-policy \
  --name otomeshon-kv \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

## Monitoring & Observability

### 1. Azure Monitor Setup

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group otomeshon-prod-rg \
  --workspace-name otomeshon-logs \
  --location eastus

# Create Application Insights
az monitor app-insights component create \
  --app otomeshon-insights \
  --location eastus \
  --resource-group otomeshon-prod-rg \
  --application-type web
```

### 2. Application Insights Integration

```python
# backend/app/core/monitoring.py
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.tracer import Tracer

class AzureMonitoring:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.log_handler = AzureLogHandler(connection_string=connection_string)
        self.trace_exporter = AzureExporter(connection_string=connection_string)
        self.tracer = Tracer(exporter=self.trace_exporter)
```

### 3. Custom Dashboards

Create Azure Monitor dashboards for:
- Application performance
- Database metrics
- Infrastructure health
- Security events
- Cost tracking

## Cost Optimization

### 1. Resource Sizing

- **Development**: Use smaller instances
- **Staging**: Medium instances
- **Production**: Right-sized instances based on load testing

### 2. Reserved Instances

```bash
# Purchase reserved instances for predictable workloads
az vm reservation create \
  --resource-group otomeshon-prod-rg \
  --reservation-order-name otomeshon-reservation \
  --sku Standard_B1ms \
  --location eastus \
  --quantity 2 \
  --reserved-resource-type VirtualMachines
```

### 3. Auto-scaling Policies

```yaml
# container-apps-scaling.yaml
scale:
  minReplicas: 2
  maxReplicas: 10
  rules:
    - name: cpu-rule
      custom:
        type: cpu
        metadata:
          type: Utilization
          value: "70"
    - name: http-rule
      http:
        metadata:
          concurrentRequests: 100
```

## Migration Checklist

### Pre-Migration

- [ ] Azure subscription setup
- [ ] Resource groups created
- [ ] Networking configured
- [ ] Key Vault setup
- [ ] Container registry created
- [ ] Database migration plan
- [ ] Backup strategy defined
- [ ] Security policies configured

### Migration

- [ ] Database migration completed
- [ ] Application configuration updated
- [ ] Container images built and pushed
- [ ] Application deployed to Azure
- [ ] DNS configured
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Load testing completed

### Post-Migration

- [ ] Performance validation
- [ ] Security testing
- [ ] Compliance validation
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Support procedures established
- [ ] Rollback procedures tested

## Troubleshooting

### Common Issues

1. **Container Registry Access**
   ```bash
   # Login to ACR
   az acr login --name otomeshonacr
   
   # Push images
   docker tag otomeshon-backend:latest otomeshonacr.azurecr.io/otomeshon-backend:latest
   docker push otomeshonacr.azurecr.io/otomeshon-backend:latest
   ```

2. **Database Connection Issues**
   - Check firewall rules
   - Verify SSL configuration
   - Test connection string

3. **Key Vault Access**
   - Verify managed identity
   - Check access policies
   - Validate secret names

4. **Monitoring Issues**
   - Check Application Insights connection
   - Verify log analytics workspace
   - Test custom metrics

### Support Resources

- [Azure Documentation](https://docs.microsoft.com/azure/)
- [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/azure/postgresql/)
- [Azure Key Vault](https://docs.microsoft.com/azure/key-vault/)

## Next Steps

1. **Review and customize** this guide for your specific requirements
2. **Set up Azure resources** following the infrastructure setup section
3. **Update application configuration** for Azure services
4. **Test migration** in a staging environment
5. **Plan production migration** with minimal downtime
6. **Monitor and optimize** after migration

For additional support or questions, refer to the Azure documentation or contact your Azure support team.
