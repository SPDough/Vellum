# Dependency Management Guide

## Overview

The Otomeshon banking platform uses a tiered dependency structure to reduce complexity and allow for flexible deployments based on feature requirements.

## Dependency Tiers

### 🟢 **Minimal** (`requirements-minimal.txt`)
**Use for:** Local development, testing, simple deployments
- FastAPI core
- Basic authentication  
- HTTP client
- **Size:** ~10 packages
- **Memory:** ~100MB

### 🔵 **Core** (`requirements-core.txt`) 
**Use for:** Standard banking operations without AI
- Minimal dependencies
- PostgreSQL database
- Neo4j knowledge graph
- Database migrations
- **Size:** ~15 packages
- **Memory:** ~300MB

### 🟡 **Banking Complete** (`requirements-banking.txt`)
**Use for:** Full banking platform with all features
- Core dependencies
- AI/LLM capabilities
- Infrastructure components
- Observability stack
- **Size:** ~40 packages  
- **Memory:** ~1GB

### 🔴 **Development** (`requirements-dev.txt`)
**Use for:** Development environment only
- Testing frameworks
- Code quality tools
- Linting and formatting
- **Size:** ~8 packages

## Component-Specific Dependencies

### AI/LLM Features (`requirements-ai.txt`)
- OpenAI/Anthropic integration
- LangChain ecosystem
- Vector operations
- Machine learning utilities

### Infrastructure (`requirements-infrastructure.txt`) 
- Kafka message streaming
- Temporal workflow engine
- Redis caching
- Drools rules engine
- Data analysis tools

### Observability (`requirements-observability.txt`)
- OpenTelemetry instrumentation
- Structured logging
- Performance monitoring
- Compliance auditing

## Installation Examples

### Minimal Development Setup
```bash
pip install -r requirements-minimal.txt
# Start with main_simple.py
```

### Standard Banking Platform
```bash
pip install -r requirements-core.txt
pip install -r requirements-ai.txt  # Optional: AI features
pip install -r requirements-observability.txt  # Optional: monitoring
```

### Complete Enterprise Setup
```bash
pip install -r requirements-banking.txt
```

### Development Environment
```bash
pip install -r requirements-banking.txt
pip install -r requirements-dev.txt
```

## Removed Dependencies

The following dependencies were removed from the original `requirements.txt` as they were not used:

### Completely Unused (Removed)
- `langgraph==0.2.45` - Not imported anywhere
- `langchain-community==0.3.5` - Not used
- `langsmith==0.1.143` - Not imported
- `xlsxwriter==3.2.0` - Imported but not used
- `gunicorn==22.0.0` - Using uvicorn instead
- `loguru==0.7.2` - Not used
- `python-jose[cryptography]==3.3.0` - Not used
- `aiohttp==3.9.5` - Not used
- `dbt-core==1.7.14` - Not used
- `dbt-duckdb==1.7.4` - Not used

### Moved to Optional Tiers
- Kafka dependencies → `requirements-infrastructure.txt`
- Temporal dependencies → `requirements-infrastructure.txt` 
- AI/LLM dependencies → `requirements-ai.txt`
- Monitoring dependencies → `requirements-observability.txt`

## Environment-Specific Recommendations

### Local Development
```bash
# Fast startup, minimal resources
pip install -r requirements-minimal.txt
```

### CI/CD Testing
```bash
# Include testing tools
pip install -r requirements-core.txt
pip install -r requirements-dev.txt
```

### Staging Environment
```bash
# Include monitoring for staging validation
pip install -r requirements-banking.txt
```

### Production Environment
```bash
# Full feature set with monitoring
pip install -r requirements-banking.txt
```

## Dependency Upgrade Strategy

### Core Dependencies
- Pin exact versions for stability
- Test thoroughly before upgrading
- Security patches applied immediately

### Optional Dependencies  
- Allow minor version flexibility
- Regular updates for feature improvements
- Backward compatibility maintained

### Development Dependencies
- Keep up-to-date with latest versions
- Automatic updates acceptable
- Focus on developer productivity

## Security Considerations

### Production Dependencies
- All production dependencies are security-scanned
- Known vulnerabilities tracked and patched
- Minimal attack surface with tiered approach

### Development Dependencies
- Development-only dependencies not deployed to production
- Separate security scanning for dev tools
- Regular cleanup of unused development packages

## Performance Impact

| Tier | Package Count | Install Time | Memory Usage | Startup Time |
|------|---------------|--------------|--------------|--------------|
| Minimal | ~10 | 30s | ~100MB | 2s |
| Core | ~15 | 60s | ~300MB | 5s |
| Banking | ~40 | 180s | ~1GB | 15s |

## Maintenance

### Monthly Tasks
- Review dependency security alerts
- Update patch versions for security fixes
- Clean up unused imports

### Quarterly Tasks  
- Evaluate new optional dependencies
- Review and update version pins
- Benchmark performance impact of updates

### Annual Tasks
- Major version upgrades planning
- Dependency architecture review
- Security audit of entire dependency tree

## Troubleshooting

### Common Issues

**Import Errors After Tier Switch:**
```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Reinstall dependencies
pip install --force-reinstall -r requirements-[tier].txt
```

**Version Conflicts:**
```bash
# Check dependency tree
pip freeze | grep [package-name]
pip show [package-name]

# Create fresh environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements-[tier].txt
```

**Missing Optional Features:**
```bash
# Check which tier provides the feature
grep -r "feature_name" requirements-*.txt

# Install additional tier
pip install -r requirements-[additional-tier].txt
```