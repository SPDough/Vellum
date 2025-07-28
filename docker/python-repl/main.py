import asyncio
import json
import logging
import os
import signal
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Dict, List, Optional

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from RestrictedPython import compile_restricted, safe_builtins, safe_globals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/repl.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Python REPL Service", version="1.0.0")

# Configuration
MAX_EXECUTION_TIME = int(os.getenv("MAX_EXECUTION_TIME", "30"))  # seconds
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "256"))  # MB
MAX_OUTPUT_LENGTH = int(os.getenv("MAX_OUTPUT_LENGTH", "10000"))  # characters
ALLOWED_MODULES = {
    'math', 'datetime', 'json', 'random', 'string', 'itertools',
    'collections', 'functools', 'operator', 'statistics',
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy',
    'sklearn', 'sympy', 'statsmodels'
}

# Execution tracking
active_executions: Dict[str, Dict[str, Any]] = {}


class ExecutionRequest(BaseModel):
    """Request model for Python code execution."""
    code: str = Field(..., description="Python code to execute")
    execution_id: Optional[str] = Field(None, description="Optional execution ID")
    timeout_seconds: Optional[int] = Field(None, description="Execution timeout in seconds")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variables to inject into execution context")


class ExecutionResponse(BaseModel):
    """Response model for Python code execution."""
    execution_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_seconds: float
    memory_usage_mb: Optional[float] = None
    variables_created: Optional[List[str]] = None
    timestamp: datetime


class ExecutionStatus(BaseModel):
    """Model for execution status."""
    execution_id: str
    status: str  # 'running', 'completed', 'failed', 'timeout'
    start_time: datetime
    execution_time_seconds: Optional[float] = None


def create_safe_globals(variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a safe global namespace for code execution."""
    safe_dict = {
        '__builtins__': {
            **safe_builtins,
            '_print_': lambda *args, **kwargs: print(*args, **kwargs),
            '_getattr_': getattr,
            '_getitem_': lambda obj, index: obj[index],
            '_getiter_': iter,
            '_write_': lambda x: x,
        }
    }
    
    # Add allowed modules
    allowed_imports = {}
    for module_name in ALLOWED_MODULES:
        try:
            if module_name == 'pandas':
                import pandas as pd
                allowed_imports['pd'] = pd
                allowed_imports['pandas'] = pd
            elif module_name == 'numpy':
                import numpy as np
                allowed_imports['np'] = np
                allowed_imports['numpy'] = np
            elif module_name == 'matplotlib':
                import matplotlib.pyplot as plt
                allowed_imports['plt'] = plt
                allowed_imports['matplotlib'] = __import__(module_name)
            elif module_name == 'seaborn':
                import seaborn as sns
                allowed_imports['sns'] = sns
                allowed_imports['seaborn'] = sns
            elif module_name == 'scipy':
                import scipy
                allowed_imports['scipy'] = scipy
            elif module_name == 'sklearn':
                import sklearn
                allowed_imports['sklearn'] = sklearn
            elif module_name == 'sympy':
                import sympy
                allowed_imports['sympy'] = sympy
            elif module_name == 'statsmodels':
                import statsmodels.api as sm
                allowed_imports['sm'] = sm
                allowed_imports['statsmodels'] = __import__(module_name)
            else:
                allowed_imports[module_name] = __import__(module_name)
        except ImportError:
            logger.warning(f"Module {module_name} not available")
    
    safe_dict.update(allowed_imports)
    
    # Add user variables if provided
    if variables:
        safe_dict.update(variables)
    
    return safe_dict


@contextmanager
def execution_timeout(seconds: int):
    """Context manager for execution timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Execution exceeded {seconds} seconds")
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def monitor_memory_usage():
    """Monitor current memory usage."""
    process = psutil.Process()
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024  # Convert to MB


async def execute_python_code(
    code: str,
    execution_id: str,
    timeout_seconds: int = MAX_EXECUTION_TIME,
    variables: Optional[Dict[str, Any]] = None
) -> ExecutionResponse:
    """Execute Python code in a restricted environment."""
    start_time = datetime.utcnow()
    initial_memory = monitor_memory_usage()
    
    # Track execution
    active_executions[execution_id] = {
        'status': 'running',
        'start_time': start_time,
        'code': code
    }
    
    try:
        # Compile the code with RestrictedPython
        compiled_code = compile_restricted(code, '<string>', 'exec')
        if compiled_code is None:
            raise ValueError("Code compilation failed - potentially unsafe code detected")
        
        # Create safe execution environment
        safe_globals_dict = create_safe_globals(variables)
        safe_locals_dict = {}
        
        # Capture stdout
        old_stdout = sys.stdout
        stdout_capture = StringIO()
        sys.stdout = stdout_capture
        
        try:
            # Execute with timeout and memory monitoring
            with execution_timeout(timeout_seconds):
                exec(compiled_code, safe_globals_dict, safe_locals_dict)
            
            # Get output
            output = stdout_capture.getvalue()
            if len(output) > MAX_OUTPUT_LENGTH:
                output = output[:MAX_OUTPUT_LENGTH] + "\n... [Output truncated]"
            
            # Check memory usage
            current_memory = monitor_memory_usage()
            memory_used = current_memory - initial_memory
            
            if memory_used > MAX_MEMORY_MB:
                logger.warning(f"Execution {execution_id} used {memory_used:.2f}MB memory")
            
            # Get variables created
            variables_created = [
                key for key in safe_locals_dict.keys() 
                if not key.startswith('_') and key not in (variables.keys() if variables else [])
            ]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update execution tracking
            active_executions[execution_id]['status'] = 'completed'
            active_executions[execution_id]['execution_time'] = execution_time
            
            return ExecutionResponse(
                execution_id=execution_id,
                success=True,
                output=output,
                execution_time_seconds=execution_time,
                memory_usage_mb=memory_used,
                variables_created=variables_created,
                timestamp=start_time
            )
            
        finally:
            sys.stdout = old_stdout
            
    except TimeoutError as e:
        active_executions[execution_id]['status'] = 'timeout'
        logger.error(f"Execution {execution_id} timed out: {str(e)}")
        return ExecutionResponse(
            execution_id=execution_id,
            success=False,
            error=f"Execution timeout: {str(e)}",
            execution_time_seconds=timeout_seconds,
            timestamp=start_time
        )
        
    except Exception as e:
        active_executions[execution_id]['status'] = 'failed'
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Execution {execution_id} failed: {error_msg}")
        
        # Include traceback for debugging (but sanitize it)
        tb = traceback.format_exc()
        if len(tb) > 1000:
            tb = tb[:1000] + "\n... [Traceback truncated]"
        
        return ExecutionResponse(
            execution_id=execution_id,
            success=False,
            error=f"{error_msg}\n\nTraceback:\n{tb}",
            execution_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
            timestamp=start_time
        )
    
    finally:
        # Clean up execution tracking after some time
        asyncio.create_task(cleanup_execution(execution_id))


async def cleanup_execution(execution_id: str, delay: int = 300):
    """Clean up execution tracking after delay."""
    await asyncio.sleep(delay)
    if execution_id in active_executions:
        del active_executions[execution_id]


@app.post("/execute", response_model=ExecutionResponse)
async def execute_code(request: ExecutionRequest):
    """Execute Python code in a sandboxed environment."""
    execution_id = request.execution_id or str(uuid.uuid4())
    timeout = request.timeout_seconds or MAX_EXECUTION_TIME
    
    # Validate timeout
    if timeout > MAX_EXECUTION_TIME:
        raise HTTPException(
            status_code=400, 
            detail=f"Timeout cannot exceed {MAX_EXECUTION_TIME} seconds"
        )
    
    # Validate code length
    if len(request.code) > 50000:  # 50KB limit
        raise HTTPException(status_code=400, detail="Code too long")
    
    logger.info(f"Executing code for execution_id: {execution_id}")
    
    result = await execute_python_code(
        code=request.code,
        execution_id=execution_id,
        timeout_seconds=timeout,
        variables=request.variables
    )
    
    return result


@app.get("/status/{execution_id}", response_model=ExecutionStatus)
async def get_execution_status(execution_id: str):
    """Get the status of a code execution."""
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = active_executions[execution_id]
    execution_time = None
    
    if execution['status'] in ['completed', 'failed', 'timeout']:
        execution_time = execution.get('execution_time')
    else:
        execution_time = (datetime.utcnow() - execution['start_time']).total_seconds()
    
    return ExecutionStatus(
        execution_id=execution_id,
        status=execution['status'],
        start_time=execution['start_time'],
        execution_time_seconds=execution_time
    )


@app.get("/active-executions")
async def get_active_executions():
    """Get list of currently active executions."""
    return {
        "active_count": len(active_executions),
        "executions": [
            {
                "execution_id": exec_id,
                "status": exec_data["status"],
                "start_time": exec_data["start_time"],
                "running_time": (datetime.utcnow() - exec_data["start_time"]).total_seconds()
            }
            for exec_id, exec_data in active_executions.items()
        ]
    }


@app.post("/cancel/{execution_id}")
async def cancel_execution(execution_id: str):
    """Cancel a running execution."""
    if execution_id not in active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # In a real implementation, you'd need to implement proper cancellation
    # For now, just mark as cancelled
    active_executions[execution_id]['status'] = 'cancelled'
    
    return {"message": f"Execution {execution_id} marked for cancellation"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    memory_usage = monitor_memory_usage()
    
    return {
        "status": "healthy",
        "memory_usage_mb": memory_usage,
        "active_executions": len(active_executions),
        "max_memory_mb": MAX_MEMORY_MB,
        "max_execution_time": MAX_EXECUTION_TIME,
        "timestamp": datetime.utcnow()
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get service capabilities and available modules."""
    return {
        "max_execution_time_seconds": MAX_EXECUTION_TIME,
        "max_memory_mb": MAX_MEMORY_MB,
        "max_output_length": MAX_OUTPUT_LENGTH,
        "allowed_modules": list(ALLOWED_MODULES),
        "features": {
            "restricted_python": True,
            "memory_monitoring": True,
            "timeout_protection": True,
            "output_capture": True,
            "variable_injection": True,
            "execution_tracking": True
        }
    }


# Cleanup old executions periodically
@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    logger.info("Python REPL Service starting up")
    
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(600)  # Every 10 minutes
            now = datetime.utcnow()
            to_remove = []
            
            for exec_id, exec_data in active_executions.items():
                if now - exec_data['start_time'] > timedelta(hours=1):
                    to_remove.append(exec_id)
            
            for exec_id in to_remove:
                del active_executions[exec_id]
                logger.info(f"Cleaned up old execution: {exec_id}")
    
    asyncio.create_task(periodic_cleanup())


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )