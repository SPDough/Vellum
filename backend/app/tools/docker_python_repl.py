import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional, Type

import httpx
from langchain.tools.base import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DockerPythonREPLInput(BaseModel):
    """Input schema for Docker Python REPL tool."""

    code: str = Field(description="Python code to execute")
    variables: Optional[Dict[str, Any]] = Field(
        default=None, description="Variables to inject into execution context"
    )
    timeout_seconds: Optional[int] = Field(
        default=30, description="Execution timeout in seconds"
    )


class DockerPythonREPLTool(BaseTool):
    """
    Custom Python REPL tool that executes code in a secure Docker container.

    This tool provides a safe environment for executing Python code as part of
    LangChain workflows, with proper sandboxing and resource limits.
    """

    name: str = "docker_python_repl"
    description: str = """
    Execute Python code in a secure Docker container. Use this tool when you need to:
    - Perform mathematical calculations
    - Analyze data with pandas/numpy
    - Create visualizations
    - Run statistical analysis
    - Process dates and times
    - Execute any Python logic

    The execution environment includes: pandas, numpy, matplotlib, seaborn, scipy,
    scikit-learn, sympy, statsmodels, and standard Python libraries.

    Input should be valid Python code as a string.
    """
    args_schema: Type[BaseModel] = DockerPythonREPLInput
    return_direct: bool = False

    repl_service_url: str = Field(default="http://localhost:8001")
    timeout: int = Field(default=60)

    def __init__(self, repl_service_url: str = "http://localhost:8001", **kwargs):
        super().__init__(**kwargs)
        self.repl_service_url = repl_service_url

    async def _arun(
        self,
        code: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Async execution of Python code in Docker container."""
        execution_id = str(uuid.uuid4())

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare request
                request_data = {
                    "code": code,
                    "execution_id": execution_id,
                    "timeout_seconds": timeout_seconds or 30,
                    "variables": variables,
                }

                logger.info(f"Executing Python code in Docker REPL: {execution_id}")

                # Execute code
                response = await client.post(
                    f"{self.repl_service_url}/execute", json=request_data
                )
                response.raise_for_status()

                result = response.json()

                if result["success"]:
                    output = result.get("output", "")
                    execution_time = result.get("execution_time_seconds", 0)
                    memory_usage = result.get("memory_usage_mb", 0)
                    variables_created = result.get("variables_created", [])

                    # Format response
                    response_parts = []
                    if output:
                        response_parts.append(f"Output:\n{output}")

                    if variables_created:
                        response_parts.append(
                            f"Variables created: {', '.join(variables_created)}"
                        )

                    response_parts.append(
                        f"Execution completed in {execution_time:.2f}s "
                        f"(Memory: {memory_usage:.1f}MB)"
                    )

                    return "\n\n".join(response_parts)
                else:
                    error = result.get("error", "Unknown error")
                    return f"Execution failed: {error}"

        except httpx.TimeoutException:
            logger.error(f"REPL execution {execution_id} timed out")
            return f"Execution timed out after {self.timeout} seconds"
        except httpx.HTTPStatusError as e:
            logger.error(f"REPL service error: {e.response.status_code}")
            return f"REPL service error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error executing Python code: {str(e)}")
            return f"Error executing Python code: {str(e)}"

    def _run(
        self,
        code: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Sync execution (runs async version)."""
        loop = None
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we can't use run_until_complete
                # Create a new task instead
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._arun(code, variables, timeout_seconds, **kwargs),
                    )
                    return future.result(timeout=self.timeout)
            else:
                return loop.run_until_complete(
                    self._arun(code, variables, timeout_seconds, **kwargs)
                )
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(self._arun(code, variables, timeout_seconds, **kwargs))

    async def check_service_health(self) -> bool:
        """Check if the REPL service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.repl_service_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def get_service_capabilities(self) -> Dict[str, Any]:
        """Get REPL service capabilities."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.repl_service_url}/capabilities")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting service capabilities: {str(e)}")
            return {}

    async def get_active_executions(self) -> Dict[str, Any]:
        """Get currently active executions."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.repl_service_url}/active-executions"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting active executions: {str(e)}")
            return {"active_count": 0, "executions": []}


# Convenience function to create the tool
def create_docker_python_repl_tool(
    repl_service_url: str = "http://localhost:8001",
) -> DockerPythonREPLTool:
    """Create a Docker Python REPL tool instance."""
    return DockerPythonREPLTool(repl_service_url=repl_service_url)


# Example usage for testing
if __name__ == "__main__":
    import asyncio

    async def test_tool():
        tool = create_docker_python_repl_tool()

        # Test health check
        healthy = await tool.check_service_health()
        print(f"Service healthy: {healthy}")

        if healthy:
            # Test capabilities
            capabilities = await tool.get_service_capabilities()
            print(f"Capabilities: {json.dumps(capabilities, indent=2)}")

            # Test code execution
            test_code = """
# Test basic calculations
import pandas as pd
import numpy as np

# Create sample data
data = {
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50]
}
df = pd.DataFrame(data)

# Calculate statistics
mean_a = df['A'].mean()
sum_b = df['B'].sum()

print(f"Mean of A: {mean_a}")
print(f"Sum of B: {sum_b}")
print(f"DataFrame shape: {df.shape}")

# Return final result
result = f"Analysis complete: Mean A = {mean_a}, Sum B = {sum_b}"
print(result)
"""

            result = await tool._arun(test_code)
            print(f"Execution result:\n{result}")

    asyncio.run(test_tool())
