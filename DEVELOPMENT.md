# Development Guide

This guide covers how to set up and run the Otomeshon application locally for development.

## Quick Start

### Option 1: Using the Development Script (Recommended)

```bash
# From the repository root
./start-dev.sh
```

This script will:
- Start the backend server on http://localhost:8000
- Start the frontend development server on http://localhost:3000
- Wait for both services to be ready
- Provide helpful information and monitoring

Press `Ctrl+C` to stop both servers.

### Option 2: Manual Setup

#### 1. Start the Backend

```bash
cd backend
python app/main_simple.py
```

The backend will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### 2. Start the Frontend (in a new terminal)

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:3000

## Development Features

### Backend (FastAPI)

The simplified backend (`app/main_simple.py`) includes:

- ✅ **Sample Data**: 100 pre-generated banking records
- ✅ **REST API**: Full CRUD operations for data sandbox
- ✅ **Interactive Docs**: Swagger UI at `/docs`
- ✅ **Health Monitoring**: Health check and metrics endpoints
- ✅ **CORS Support**: Configured for frontend development
- ✅ **No External Dependencies**: Runs without PostgreSQL, Redis, etc.

#### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/api/v1/data-sandbox/records` | GET | Get paginated records |
| `/api/v1/data-sandbox/stats` | GET | Get data statistics |
| `/api/v1/data-sandbox/sources` | GET | Get available data sources |
| `/api/v1/data-sandbox/filter` | POST | Advanced filtering |
| `/api/v1/data-sandbox/export` | POST | Export data |
| `/docs` | GET | Interactive API documentation |

### Frontend (React + Vite)

The frontend development server includes:

- ✅ **Hot Reloading**: Instant updates on file changes
- ✅ **TypeScript Support**: Full type checking
- ✅ **Modern React**: React 18 with hooks
- ✅ **Material-UI**: Pre-configured component library
- ✅ **Development Tools**: React DevTools support

## Testing

### Run All Tests

```bash
# Frontend tests
cd frontend && npm run test:run

# Backend tests  
cd backend && python -m pytest tests/ -q

# Or run both with the setup command
cd ~/repos/Vellum/frontend && npm run test:run && cd ~/repos/Vellum/backend && python -m pytest tests/ -q
```

### Test Coverage

- **Frontend**: 2 tests (React component rendering, basic unit tests)
- **Backend**: 15 tests (API endpoints, core functionality)

## Linting

### Run Linting

```bash
# Frontend linting (ESLint)
cd frontend && npm run lint

# Backend linting (Black + isort)
cd backend && python -m black --check . && python -m isort --check-only .

# Or run both with the setup command
cd ~/repos/Vellum/frontend && npm run lint && cd ~/repos/Vellum/backend && python -m black --check . && python -m isort --check-only .
```

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

**Python version issues:**
```bash
# Check Python version (should be 3.12.8)
python --version

# If wrong version, set it with pyenv
cd ~/repos/Vellum && pyenv local 3.12.8
```

**Missing dependencies:**
```bash
cd backend && pip install -r requirements.txt
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9
```

**Node.js version issues:**
```bash
# Check Node.js version (should be 20+)
node --version
```

**Missing dependencies:**
```bash
cd frontend && npm install
```

**ESLint configuration issues:**
```bash
# The project uses ESLint 9.x with flat config
# Configuration is in eslint.config.js
cd frontend && npm run lint:fix
```

### General Issues

**Clean restart:**
```bash
# Kill all development processes
pkill -f "python.*main_simple"
pkill -f "node.*dev"

# Restart with the development script
./start-dev.sh
```

## Development Workflow

1. **Start Development Environment**
   ```bash
   ./start-dev.sh
   ```

2. **Make Changes**
   - Backend changes: Edit files in `backend/app/`
   - Frontend changes: Edit files in `frontend/src/`

3. **Test Changes**
   ```bash
   # Run tests
   npm run test:run  # Frontend
   python -m pytest tests/ -q  # Backend
   ```

4. **Lint Code**
   ```bash
   npm run lint  # Frontend
   python -m black . && python -m isort .  # Backend
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Your commit message"
   ```

## Production Deployment

For production deployment with all services (PostgreSQL, Redis, Neo4j, etc.), use Docker Compose:

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Development with all services
docker-compose -f docker-compose.dev.yml up -d
```

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **React DevTools**: Install browser extension for debugging
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Vite Documentation**: https://vitejs.dev/
- **Material-UI Documentation**: https://mui.com/