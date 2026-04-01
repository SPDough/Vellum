# Docker Python REPL for LangChain Workflows

This directory contains a secure, containerized Python REPL service designed specifically for LangChain workflow executions. The service provides a sandboxed environment for running Python code with proper resource limits and security measures.

## 🔧 Features

### Security & Sandboxing
- **RestrictedPython**: Uses RestrictedPython for safe code execution
- **Resource Limits**: CPU (0.5 cores), Memory (512MB), Execution time (30s)
- **Non-root User**: Runs as dedicated `repluser` for security
- **Read-only Container**: Minimal write access
- **Network Isolation**: Runs in isolated Docker network

### Python Libraries Available
- **Data Science**: pandas, numpy, matplotlib, seaborn, scipy, scikit-learn
- **Math & Stats**: sympy, statsmodels
- **Standard Libraries**: math, datetime, json, statistics, etc.

### Monitoring & Management
- **Health Checks**: Built-in health monitoring
- **Execution Tracking**: Track active executions and performance
- **Logging**: Comprehensive logging to files and stdout
- **Automatic Cleanup**: Memory and execution cleanup

## 🚀 Quick Start

### 1. Start the Service
```bash
cd /path/to/project
./scripts/start_repl_service.sh
```

### 2. Verify Service is Running
```bash
curl http://localhost:8001/health
```

### 3. Check Capabilities
```bash
curl http://localhost:8001/capabilities
```

## 📡 API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /capabilities` - Available features and limits
- `GET /active-executions` - Currently running executions

### Code Execution
- `POST /execute` - Execute Python code
- `GET /status/{execution_id}` - Get execution status
- `POST /cancel/{execution_id}` - Cancel running execution

### Example Request
```json
{
  "code": "import pandas as pd\\ndf = pd.DataFrame({'a': [1,2,3]})\\nprint(df.mean())",
  "timeout_seconds": 30,
  "variables": {"input_data": [1, 2, 3, 4, 5]}
}
```

### Example Response
```json
{
  "execution_id": "uuid-here",
  "success": true,
  "output": "a    2.0\\ndtype: float64",
  "execution_time_seconds": 0.15,
  "memory_usage_mb": 45.2,
  "variables_created": ["df"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🛠 Development

### Building the Image
```bash
cd docker/python-repl
docker build -t otomeshon-python-repl:latest .
```

### Running with Docker Compose
```bash
docker-compose up -d
```

### Viewing Logs
```bash
docker logs otomeshon-python-repl
```

### Stopping the Service
```bash
docker-compose down
```

## ⚙️ Configuration

### Environment Variables
- `MAX_EXECUTION_TIME`: Maximum execution time (default: 30s)
- `MAX_MEMORY_MB`: Maximum memory usage (default: 256MB)
- `MAX_OUTPUT_LENGTH`: Maximum output length (default: 10000 chars)

### Docker Resource Limits
- CPU: 0.5 cores
- Memory: 512MB
- Execution timeout: 30 seconds

## 🔒 Security Considerations

### What's Protected
✅ **Code Injection**: RestrictedPython prevents dangerous operations  
✅ **Resource Exhaustion**: CPU, memory, and time limits  
✅ **File System Access**: Limited write access  
✅ **Network Access**: Controlled network environment  
✅ **Privilege Escalation**: Non-root execution  

### What's Allowed
- Safe Python operations and calculations
- Data analysis with pandas, numpy, etc.
- Mathematical computations
- Statistical analysis
- Basic visualizations (matplotlib, seaborn)

### What's Restricted
- File system modifications (except logs)
- Network requests (except internal)
- System calls
- Import of unsafe modules
- Long-running operations (>30s)

## 🧪 Testing

### Basic Test
```python
import requests

response = requests.post('http://localhost:8001/execute', json={
    'code': '''
import pandas as pd
data = {'x': [1, 2, 3], 'y': [4, 5, 6]}
df = pd.DataFrame(data)
print(f"Shape: {df.shape}")
print(df.head())
''',
    'timeout_seconds': 10
})

print(response.json())
```

### Performance Test
```bash
# Run multiple concurrent executions
for i in {1..5}; do
  curl -X POST http://localhost:8001/execute \
    -H "Content-Type: application/json" \
    -d '{"code":"import time; time.sleep(1); print(f\"Task {i} done\")"}' &
done
wait
```

## 🔗 Integration with LangChain

The service integrates with LangChain through the `DockerPythonREPLTool` class:

```python
from app.tools.docker_python_repl import create_docker_python_repl_tool

# Create the tool
repl_tool = create_docker_python_repl_tool("http://localhost:8001")

# Use with LangChain agent
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools=[repl_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Execute workflow
result = agent.run("Calculate the mean and standard deviation of [1,2,3,4,5]")
```

## 📊 Monitoring

### Health Monitoring
The service includes comprehensive health monitoring:
- Memory usage tracking
- Active execution counting
- Response time monitoring
- Error rate tracking

### Logs
Logs are available in multiple locations:
- Container logs: `docker logs otomeshon-python-repl`
- Log files: `/app/logs/repl.log` (inside container)
- Volume mount: `repl_logs` volume

### Metrics
Key metrics tracked:
- Execution count and success rate
- Average execution time
- Memory usage patterns
- Error frequency and types

## 🚨 Troubleshooting

### Service Won't Start
1. Check Docker is running: `docker info`
2. Check port availability: `lsof -i :8001`
3. Check logs: `docker logs otomeshon-python-repl`

### Memory Issues
1. Check resource limits: `docker stats otomeshon-python-repl`
2. Adjust limits in `docker-compose.yml`
3. Monitor active executions: `curl http://localhost:8001/active-executions`

### Execution Timeouts
1. Reduce complexity of Python code
2. Increase timeout limits (with caution)
3. Check for infinite loops in code

### Permission Errors
1. Verify non-root user setup
2. Check volume permissions
3. Review security constraints

## 📈 Performance Tuning

### For High Load
- Increase resource limits in `docker-compose.yml`
- Scale horizontally with multiple containers
- Use Redis for execution result caching
- Implement connection pooling

### For Better Security
- Enable SELinux/AppArmor if available
- Use custom seccomp profiles
- Implement additional network restrictions
- Add audit logging

## 🔄 Updates & Maintenance

### Updating Dependencies
1. Modify `requirements.txt`
2. Rebuild image: `docker build -t otomeshon-python-repl:latest .`
3. Restart service: `docker-compose up -d`

### Backup & Recovery
- Log volumes: `repl_logs` and `repl_executions`
- Configuration: `docker-compose.yml` and `Dockerfile`
- Custom code: Service implementation in `main.py`

This Python REPL service provides a secure, scalable foundation for executing Python code within LangChain workflows while maintaining proper isolation and resource controls.