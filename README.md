# Otomeshon - Banking Operations Automation Platform

> Middle office automations and back office validations for custodian banks — AI-powered post-trade processing, NAV validation, and data sandbox capabilities

![Otomeshon Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Overview

Otomeshon is a banking operations platform focused on **middle office automations** and **back office validations**. It streamlines post-trade processing through AI-powered workflows, supports NAV and custody validation, and provides advanced data analysis through an integrated Data Sandbox.

### Key Features

- 🏦 **Banking Operations Automation** - Streamlined post-trade processing workflows
- 📊 **Data Sandbox** - Advanced data analysis with TanStack Table integration
- 🤖 **AI-Powered Workflows** - LangChain integration for intelligent processing
- 📈 **Real-time Analytics** - Live data visualization and monitoring
- 🔐 **Enterprise Security** - Production-ready with comprehensive monitoring
- 🐳 **Cloud-Native** - Docker containers with Kubernetes support

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.12+ (for local development)

### 1. Clone and Start

```bash
git clone https://github.com/your-username/otomeshon.git
cd otomeshon
cp .env.example .env
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Monitoring (Grafana)**: http://localhost:3001 (admin/admin)

### 3. Test the Data Sandbox

The Data Sandbox comes pre-loaded with 100 sample banking records:

```bash
# View sample data
curl http://localhost:8000/api/v1/data-sandbox/records

# Get statistics
curl http://localhost:8000/api/v1/data-sandbox/stats
```

## 📊 Data Sandbox Features

The core feature of Otomeshon is the advanced Data Sandbox for banking data analysis:

### ✅ Implemented Features

- **Advanced Data Grid** with TanStack Table
- **Real-time Filtering & Sorting** 
- **Pagination & Search**
- **Data Export** (CSV, Excel)
- **Chart Visualizations** (Line, Bar, Pie)
- **WebSocket Real-time Updates**
- **Multiple Data Sources** (Workflow, API, MCP, Manual)

### Sample Data

The sandbox includes realistic banking data:
- **Trade Records** - Post-trade settlement data
- **SOP Documents** - Standard Operating Procedures
- **Analytics Reports** - Risk and compliance metrics
- **Customer Data** - Transaction histories

## 🏗️ Architecture

### Frontend Stack
- **React 18** with TypeScript
- **Material-UI (MUI)** for components
- **TanStack Table** for advanced data grids
- **Recharts** for data visualization
- **Zustand** for state management
- **React Query** for data fetching

### Backend Stack
- **FastAPI** with Python 3.12
- **SQLAlchemy** for database ORM
- **Pydantic** for data validation
- **LangChain** for AI workflows
- **WebSocket** support for real-time updates

### Infrastructure
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **Neo4j** - Graph database for relationships
- **Apache Kafka** - Event streaming
- **Prometheus + Grafana** - Monitoring
- **Docker** - Containerization

## 🐳 Development Setup

### Local Development (without Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker Development
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## 🚀 Production Deployment

### Using Docker Compose
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Or use the deployment script
./scripts/deploy.sh
```

### Using the Deployment Script
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

The deployment script includes:
- Automated health checks
- Database migrations
- Backup creation
- Service monitoring
- Rollback capabilities

## 📈 Monitoring

### Grafana Dashboards
- **System Metrics** - CPU, Memory, Disk usage
- **Application Metrics** - Request rates, response times
- **Database Metrics** - Connection pools, query performance
- **Custom Business Metrics** - Data sandbox usage, workflow metrics

### Prometheus Metrics
Access metrics at: http://localhost:9090

Key metrics:
- `otomeshon_websocket_connections_total`
- `otomeshon_data_sandbox_records_total`
- `otomeshon_data_exports_total`

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Run full test suite
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📚 API Documentation

### Interactive API Docs
Visit http://localhost:8000/docs for full API documentation with interactive testing.

### Key Endpoints

#### Data Sandbox API
- `GET /api/v1/data-sandbox/records` - Get paginated records
- `POST /api/v1/data-sandbox/filter` - Advanced filtering
- `GET /api/v1/data-sandbox/stats` - Get statistics
- `GET /api/v1/data-sandbox/sources` - Get data sources
- `POST /api/v1/data-sandbox/export` - Export data

#### Health & Monitoring
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

## 🔧 Configuration

### Environment Variables

#### Application Settings
```env
ENVIRONMENT=development|production
SECRET_KEY=your-secret-key
DEBUG=true|false
LOG_LEVEL=debug|info|warning|error
```

#### Database Configuration
```env
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
NEO4J_URI=bolt://host:port
```

#### AI API Keys
```env
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript/Python type hints
- Write tests for new features
- Update documentation
- Follow the existing code style

## 📋 Project Status

### ✅ Completed Features
- [x] Data Sandbox API with 100 sample records
- [x] Docker containerization
- [x] CI/CD pipeline with GitHub Actions
- [x] Monitoring with Prometheus + Grafana
- [x] Production deployment infrastructure
- [x] Comprehensive API documentation
- [x] Azure migration planning and documentation

### 🚧 In Progress
- [ ] React frontend debugging (mounting issues)
- [ ] Authentication system
- [ ] Error handling improvements
- [ ] SSL certificate setup

### 📋 Planned Features
- [ ] User management system
- [ ] Advanced workflow builder
- [ ] Real-time collaboration
- [ ] Advanced AI integrations
- [ ] Mobile responsive design
- [ ] Azure production deployment (see [Azure Migration Documentation](docs/azure_migration/README.md))

## 🐛 Known Issues

1. **Frontend React Mounting** - The React frontend has import conflicts preventing proper mounting
2. **Authentication** - Currently using demo auto-login for development
3. **HTTPS** - Production deployment needs SSL certificate configuration

## 🚀 Production Deployment

### Azure Migration
All Azure migration planning and documentation has been organized in the [`docs/azure_migration/`](docs/azure_migration/README.md) folder to keep development work uncluttered. This includes:

- 📋 Migration planning documents
- 🔧 Azure configuration files
- 🚀 Deployment scripts
- 💰 Cost considerations

**Note**: Azure resources will incur costs when created. The migration folder is for planning only - use when ready for production deployment.

## 📞 Support

For questions and support:
- Create an issue in this repository
- Check the [API Documentation](http://localhost:8000/docs)
- Review the [Deployment Guide](docs/DEPLOYMENT.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://reactjs.org/) and [Material-UI](https://mui.com/)
- Data grids by [TanStack Table](https://tanstack.com/table)
- AI workflows with [LangChain](https://langchain.com/)
- Monitoring by [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/)

---

**Otomeshon** - Automating the future of banking operations 🏦✨

*This repository has been verified for development access and linting capabilities.*
