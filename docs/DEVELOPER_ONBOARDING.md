# Otomeshon Developer Onboarding Guide

Welcome to the Otomeshon banking operations automation platform! This guide will help you get up and running as a developer on the project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Environment Setup](#development-environment-setup)
- [Project Overview](#project-overview)
- [First Steps](#first-steps)
- [Development Workflow](#development-workflow)
- [Code Walkthrough](#code-walkthrough)
- [Testing Guidelines](#testing-guidelines)
- [Contribution Guidelines](#contribution-guidelines)
- [Getting Help](#getting-help)

## Prerequisites

Before you begin, ensure you have the following installed on your development machine:

### Required Software

- **Python 3.11+**: Backend development
- **Node.js 18+**: Optional; only if you also work on the custodian portal (separate repo)
- **Docker & Docker Compose**: For running services
- **Git**: Version control
- **PostgreSQL 14+**: Primary database
- **Redis 6+**: Caching and sessions
- **Neo4j 5+**: Knowledge graph database

### Recommended Tools

- **VS Code**: IDE with Python and TypeScript extensions
- **Postman/Insomnia**: API testing
- **pgAdmin**: PostgreSQL administration
- **Neo4j Browser**: Graph database exploration
- **Redis CLI**: Redis debugging

### Account Setup

1. **GitHub Access**: Ensure you have access to the repository
2. **API Keys**: Request access to development API keys for:
   - OpenAI (for LLM features)
   - Any external data providers
3. **Database Access**: Development database credentials

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/SPDough/Vellum.git
cd Vellum
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. User interface (custodian portal)

The product UI is developed in the **custodian portal** repository (not in this `Vellum` tree). Clone that repo and follow its README for Node, Vite, and Tailwind setup.

### 4. Environment configuration

Create a backend environment file:

#### Backend Environment (.env)
```bash
# Copy example environment file
cp backend/.env.example backend/.env

# Edit the .env file with your configuration
# Key variables to set:
DATABASE_URL=postgresql://user:password@localhost:5432/otomeshon_dev
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

### 5. Database Setup

#### Option A: Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# This will start:
# - PostgreSQL on port 5432
# - Redis on port 6379
# - Neo4j on port 7687 (HTTP: 7474)
```

#### Option B: Local Installation
```bash
# PostgreSQL
createdb otomeshon_dev

# Run migrations
cd backend
python -m alembic upgrade head

# Neo4j - Create database and run initial setup
# (Use Neo4j Browser at http://localhost:7474)
```

### 6. Verify Installation

#### Test Backend
```bash
cd backend

# Run tests
python -m pytest

# Start development server
python -m uvicorn app.main:app --reload --port 8000

# Test API endpoint
curl http://localhost:8000/health
```

### 7. Development Tools Setup

#### VS Code Extensions
Install these recommended extensions:
- Python
- Pylance
- TypeScript and JavaScript Language Features
- ES7+ React/Redux/React-Native snippets
- Prettier - Code formatter
- ESLint
- GitLens

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

## Project Overview

### Architecture Summary

Otomeshon is a microservices-based platform with:

- **UI**: Custodian portal (separate repository); this repo is backend-focused
- **Backend**: FastAPI Python application
- **Databases**: PostgreSQL (primary), Neo4j (graph), Redis (cache)
- **Key Features**: Data Sandbox, AI Agents, Workflow Automation, Knowledge Graph

### Directory Structure

```
Vellum/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and utilities
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── docs/                   # Documentation
├── docker-compose.*.yml    # Docker Compose stacks (minimal / dev / prod)
└── README.md              # Project overview
```

## First Steps

### 1. Explore the Codebase

Start by understanding the key components:

#### Backend Entry Points
- `backend/app/main.py`: Full-featured application
- `backend/app/main_simple.py`: Simplified version for development

#### Key Services
- `DataSandboxService`: Data management and querying
- `MCPService`: External data provider integration
- `Neo4jService`: Knowledge graph operations
- `LLMService`: AI model interactions

#### UI (custodian portal)

Screens such as layout, data sandbox, agents, and knowledge graph live in the **custodian portal** repository.

### 2. Run Your First Test

```bash
# Backend test
cd backend
python -m pytest tests/test_health.py -v
```

### 3. Make Your First Change

Try making a small change to verify your setup:

#### Backend Change
```python
# In backend/app/api/endpoints/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Hello from [Your Name]!",  # Add your name here
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 4. Test Your Changes

```bash
# Restart backend
cd backend
python -m uvicorn app.main:app --reload

# Test the change
curl http://localhost:8000/health
```

## Development Workflow

### 1. Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### 2. Code Quality Checks

Before committing, always run:

```bash
# Backend linting and formatting
cd backend
python -m black .
python -m isort .
python -m flake8

```

### 3. Testing

```bash
# Run all backend tests
cd backend
python -m pytest

# Run specific test file
python -m pytest tests/test_data_sandbox.py -v
```

### 4. Database Migrations

When you modify database models:

```bash
# Create migration
cd backend
python -m alembic revision --autogenerate -m "Add new table"

# Apply migration
python -m alembic upgrade head
```

## Code Walkthrough

### Backend Architecture

#### 1. API Endpoints Structure
```python
# app/api/endpoints/data_sandbox.py
from fastapi import APIRouter, Depends
from app.services.data_sandbox_service import DataSandboxService

router = APIRouter(prefix="/data-sandbox", tags=["data-sandbox"])

@router.get("/sources")
async def list_data_sources(
    service: DataSandboxService = Depends(get_data_sandbox_service)
):
    return await service.list_sources()
```

#### 2. Service Layer Pattern
```python
# app/services/data_sandbox_service.py
class DataSandboxService:
    def __init__(self, db: Session):
        self.db = db
    
    async def list_sources(self) -> List[DataSource]:
        return self.db.query(DataSource).filter(
            DataSource.status == "active"
        ).all()
```

#### 3. Database Models
```python
# app/models/data_source.py
from sqlalchemy import Column, String, DateTime, Integer
from app.core.database import Base

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Frontend Architecture

#### 1. Component Structure
```typescript
// components/DataSandbox/DataTable.tsx
interface DataTableProps {
  data: DataRecord[];
  onRowClick?: (row: DataRecord) => void;
}

const DataTable: React.FC<DataTableProps> = ({ data, onRowClick }) => {
  // Component implementation
};
```

#### 2. Custom Hooks
```typescript
// hooks/useDataSandbox.ts
export const useDataSources = () => {
  return useQuery({
    queryKey: ['dataSources'],
    queryFn: () => apiClient.get<DataSource[]>('/api/v1/data-sandbox/sources')
  });
};
```

#### 3. State Management
```typescript
// store/auth.ts
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  login: async (credentials) => {
    // Login implementation
  }
}));
```

## Testing Guidelines

### Backend Testing

#### 1. Unit Tests
```python
# tests/test_data_sandbox_service.py
import pytest
from app.services.data_sandbox_service import DataSandboxService

@pytest.fixture
def service():
    return DataSandboxService(db=mock_db)

def test_list_sources(service):
    sources = service.list_sources()
    assert len(sources) > 0
    assert sources[0].status == "active"
```

#### 2. Integration Tests
```python
# tests/test_api_endpoints.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Frontend Testing

#### 1. Component Tests
```typescript
// tests/components/DataTable.test.tsx
import { render, screen } from '@testing-library/react';
import { DataTable } from '../components/DataSandbox/DataTable';

test('renders data table with data', () => {
  const mockData = [{ id: '1', name: 'Test' }];
  render(<DataTable data={mockData} />);
  
  expect(screen.getByText('Test')).toBeInTheDocument();
});
```

#### 2. Hook Tests
```typescript
// tests/hooks/useDataSandbox.test.ts
import { renderHook } from '@testing-library/react';
import { useDataSources } from '../hooks/useDataSandbox';

test('fetches data sources', async () => {
  const { result } = renderHook(() => useDataSources());
  
  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true);
  });
});
```

## Contribution Guidelines

### 1. Code Style

#### Python (Backend)
- Follow PEP 8 style guide
- Use Black for formatting
- Use isort for import sorting
- Maximum line length: 88 characters
- Use type hints for all functions

#### TypeScript (Frontend)
- Follow ESLint configuration
- Use Prettier for formatting
- Prefer functional components with hooks
- Use TypeScript interfaces for all props

### 2. Commit Messages

Follow conventional commit format:
```
feat: add new data export functionality
fix: resolve WebSocket connection issue
docs: update API documentation
test: add unit tests for DataSandboxService
refactor: improve error handling in MCP service
```

### 3. Pull Request Process

1. **Create Feature Branch**: `git checkout -b feature/description`
2. **Make Changes**: Implement your feature with tests
3. **Run Quality Checks**: Linting, formatting, tests
4. **Create PR**: Use the provided PR template
5. **Code Review**: Address feedback from reviewers
6. **Merge**: Squash and merge after approval

### 4. Documentation

- Update relevant documentation for new features
- Add docstrings to all Python functions
- Add JSDoc comments for complex TypeScript functions
- Update API documentation for new endpoints

## Getting Help

### 1. Documentation Resources

- **Architecture Guide**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Frontend Guide**: `docs/FRONTEND_GUIDE.md`
- **Database Schema**: `docs/DATABASE_SCHEMA.md`

### 2. Development Resources

- **Troubleshooting**: `DEVELOPMENT.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Testing Guide**: Check test files for examples

### 3. Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Code Reviews**: For technical discussions

### 4. Common Issues and Solutions

#### Backend Issues

**Issue**: Import errors when starting the server
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Issue**: Database connection errors
```bash
# Solution: Check database is running and credentials are correct
docker-compose -f docker-compose.dev.yml up -d postgres
```

#### UI (custodian portal) issues

Use the custodian portal repository’s troubleshooting docs for Node, Vite, and browser tooling.

### 5. Development Tips

1. **Use the Simplified Backend**: Start with `main_simple.py` for easier development
2. **Hot Reloading**: Backend supports hot reload when run under `uvicorn --reload`
3. **Database Seeding**: Use the provided seed scripts for test data
4. **API Testing**: Use the interactive docs at `http://localhost:8000/docs`
5. **Browser DevTools**: Use browser devtools while exercising the portal against this API

## Next Steps

After completing this onboarding:

1. **Explore Features**: Try out the Data Sandbox, Agents, and Knowledge Graph
2. **Read the Code**: Understand the existing patterns and conventions
3. **Pick a Task**: Look for "good first issue" labels in GitHub
4. **Ask Questions**: Don't hesitate to ask for help or clarification
5. **Contribute**: Start with small improvements and work up to larger features

Welcome to the team! We're excited to have you contributing to Otomeshon.
