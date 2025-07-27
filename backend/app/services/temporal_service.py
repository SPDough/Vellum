import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TemporalService:
    """Temporal service for workflow orchestration and scheduling."""

    def __init__(self) -> None:
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.activities: Dict[str, Callable] = {}
        self.scheduled_workflows: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start Temporal service."""
        try:
            logger.info("Starting Temporal service...")
            self.running = True

            # Register default activities
            await self._register_default_activities()

            # Start workflow scheduler
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())

            logger.info("Temporal service started successfully")

        except Exception as e:
            logger.error(f"Failed to start Temporal service: {e}")
            raise

    async def stop(self) -> None:
        """Stop Temporal service."""
        try:
            logger.info("Stopping Temporal service...")
            self.running = False

            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass

            logger.info("Temporal service stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping Temporal service: {e}")

    async def _register_default_activities(self) -> None:
        """Register default workflow activities."""
        self.activities.update(
            {
                "mcp_call": self._mcp_call_activity,
                "data_transform": self._data_transform_activity,
                "data_filter": self._data_filter_activity,
                "send_notification": self._send_notification_activity,
                "store_data": self._store_data_activity,
                "wait_for_condition": self._wait_for_condition_activity,
            }
        )

    async def register_workflow(
        self, workflow_id: str, workflow_definition: Dict[str, Any]
    ) -> bool:
        """Register a workflow for execution."""
        try:
            logger.info(f"Registering workflow: {workflow_id}")

            self.workflows[workflow_id] = {
                "id": workflow_id,
                "definition": workflow_definition,
                "registered_at": datetime.utcnow(),
                "executions": [],
            }

            return True

        except Exception as e:
            logger.error(f"Failed to register workflow {workflow_id}: {e}")
            return False

    async def execute_workflow(
        self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a workflow and return execution ID."""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not registered")

            execution_id = str(uuid4())
            execution = {
                "id": execution_id,
                "workflow_id": workflow_id,
                "status": "RUNNING",
                "input_data": input_data or {},
                "output_data": {},
                "started_at": datetime.utcnow(),
                "completed_at": None,
                "error": None,
                "steps": [],
            }

            self.workflows[workflow_id]["executions"].append(execution)

            # Start workflow execution in background
            asyncio.create_task(self._execute_workflow_steps(execution))

            logger.info(f"Started workflow execution: {execution_id}")
            return execution_id

        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise

    async def _execute_workflow_steps(self, execution: Dict[str, Any]) -> None:
        """Execute workflow steps."""
        try:
            workflow_id = execution["workflow_id"]
            workflow_def = self.workflows[workflow_id]["definition"]

            # Simple sequential execution for demo
            current_data = execution["input_data"]

            for i, node in enumerate(workflow_def.get("nodes", [])):
                step_id = str(uuid4())
                step = {
                    "id": step_id,
                    "node_id": node["id"],
                    "node_type": node.get("type", "unknown"),
                    "status": "RUNNING",
                    "started_at": datetime.utcnow(),
                    "completed_at": None,
                    "input": current_data,
                    "output": None,
                    "error": None,
                }

                execution["steps"].append(step)

                try:
                    # Execute node activity
                    result = await self._execute_node(node, current_data)

                    step["status"] = "COMPLETED"
                    step["completed_at"] = datetime.utcnow()
                    step["output"] = result
                    current_data = result

                except Exception as e:
                    step["status"] = "FAILED"
                    step["completed_at"] = datetime.utcnow()
                    step["error"] = str(e)

                    execution["status"] = "FAILED"
                    execution["completed_at"] = datetime.utcnow()
                    execution["error"] = f"Step {i+1} failed: {str(e)}"
                    return

            # Workflow completed successfully
            execution["status"] = "COMPLETED"
            execution["completed_at"] = datetime.utcnow()
            execution["output_data"] = current_data

            logger.info(f"Workflow execution completed: {execution['id']}")

        except Exception as e:
            execution["status"] = "FAILED"
            execution["completed_at"] = datetime.utcnow()
            execution["error"] = str(e)
            logger.error(f"Workflow execution failed: {execution['id']}: {e}")

    async def _execute_node(
        self, node: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow node."""
        node_type = node.get("type", "unknown")
        node_config = node.get("config", {})

        if node_type == "FIBO_MAPPING":
            return await self._fibo_mapping_activity(node_config, input_data)
        elif node_type == "MCP_CALL":
            return await self._mcp_call_activity(node_config, input_data)
        elif node_type == "TRANSFORM":
            return await self._data_transform_activity(node_config, input_data)
        elif node_type == "FILTER":
            return await self._data_filter_activity(node_config, input_data)
        elif node_type == "DATA_SINK":
            return await self._store_data_activity(node_config, input_data)
        else:
            # Default pass-through
            return input_data

    # Activity implementations
    async def _mcp_call_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """MCP server call activity."""
        try:
            # Mock MCP call for demo
            await asyncio.sleep(0.1)  # Simulate network call

            server_id = config.get("mcp_server_id", "unknown")
            tool_name = config.get("endpoint_id", "unknown_tool")
            parameters = config.get("parameters", {})

            # Merge input data with parameters
            merged_params = {**parameters, **input_data}

            # Mock response
            result = {
                "server_id": server_id,
                "tool_name": tool_name,
                "result": {
                    "status": "success",
                    "data": merged_params,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            return result

        except Exception as e:
            logger.error(f"MCP call activity failed: {e}")
            raise

    async def _data_transform_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Data transformation activity."""
        try:
            # Mock transformation
            transform_code = config.get("transformation_code", "")

            # Simple transformation for demo
            result = {
                "transformed": True,
                "original_data": input_data,
                "transform_applied": (
                    transform_code[:50] + "..."
                    if len(transform_code) > 50
                    else transform_code
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"Data transform activity failed: {e}")
            raise

    async def _data_filter_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Data filtering activity."""
        try:
            filter_expr = config.get("filter_expression", "true")

            # Mock filtering - always pass for demo
            result = {
                "filtered": True,
                "filter_expression": filter_expr,
                "passed_filter": True,
                "data": input_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"Data filter activity failed: {e}")
            raise

    async def _send_notification_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification activity."""
        try:
            # Mock notification
            result = {
                "notification_sent": True,
                "channel": config.get("channel", "email"),
                "recipient": config.get("recipient", "admin@example.com"),
                "message": f"Workflow notification: {input_data}",
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"Send notification activity failed: {e}")
            raise

    async def _store_data_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store data activity."""
        try:
            destination = config.get("destination_type", "database")

            # Mock data storage
            result = {
                "data_stored": True,
                "destination": destination,
                "record_id": str(uuid4()),
                "stored_data": input_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"Store data activity failed: {e}")
            raise

    async def _wait_for_condition_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Wait for condition activity."""
        try:
            wait_seconds = config.get("wait_seconds", 1)
            await asyncio.sleep(wait_seconds)

            result = {
                "wait_completed": True,
                "waited_seconds": wait_seconds,
                "data": input_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"Wait for condition activity failed: {e}")
            raise

    async def _fibo_mapping_activity(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """FIBO ontology mapping activity."""
        try:
            from app.services.langgraph_service import get_langgraph_service
            
            langgraph_service = await get_langgraph_service()
            
            workflow_id = await langgraph_service.create_fibo_mapping_workflow()
            result = await langgraph_service.execute_workflow(workflow_id, input_data)
            
            fibo_result = {
                "fibo_mapping_completed": True,
                "workflow_id": workflow_id,
                "mapped_positions": result.get("data", {}).get("fibo_positions", []),
                "mapping_results": result.get("data", {}).get("mapping_results", []),
                "messages": result.get("messages", []),
                "errors": result.get("errors", []),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            return fibo_result

        except Exception as e:
            logger.error(f"FIBO mapping activity failed: {e}")
            return {
                "fibo_mapping_completed": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def schedule_workflow(
        self,
        workflow_id: str,
        schedule: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Schedule a workflow for periodic execution."""
        schedule_id = str(uuid4())

        self.scheduled_workflows[schedule_id] = {
            "id": schedule_id,
            "workflow_id": workflow_id,
            "schedule": schedule,
            "input_data": input_data or {},
            "created_at": datetime.utcnow(),
            "last_run": None,
            "next_run": self._calculate_next_run(schedule),
            "enabled": True,
        }

        logger.info(f"Scheduled workflow {workflow_id} with schedule: {schedule}")
        return schedule_id

    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time based on schedule string."""
        # Simple implementation - in practice would use cron-like parsing
        now = datetime.utcnow()

        if schedule.startswith("every_"):
            interval = schedule.replace("every_", "")
            if interval.endswith("_minutes"):
                minutes = int(interval.replace("_minutes", ""))
                return now + timedelta(minutes=minutes)
            elif interval.endswith("_hours"):
                hours = int(interval.replace("_hours", ""))
                return now + timedelta(hours=hours)
            elif interval.endswith("_days"):
                days = int(interval.replace("_days", ""))
                return now + timedelta(days=days)

        # Default to 1 hour
        return now + timedelta(hours=1)

    async def _scheduler_loop(self) -> None:
        """Background scheduler loop."""
        while self.running:
            try:
                now = datetime.utcnow()

                for schedule_id, schedule_info in list(
                    self.scheduled_workflows.items()
                ):
                    if not schedule_info.get("enabled", True):
                        continue

                    if schedule_info["next_run"] <= now:
                        # Execute scheduled workflow
                        workflow_id = schedule_info["workflow_id"]
                        input_data = schedule_info["input_data"]

                        try:
                            execution_id = await self.execute_workflow(
                                workflow_id, input_data
                            )
                            schedule_info["last_run"] = now
                            schedule_info["next_run"] = self._calculate_next_run(
                                schedule_info["schedule"]
                            )

                            logger.info(
                                f"Executed scheduled workflow {workflow_id}: {execution_id}"
                            )

                        except Exception as e:
                            logger.error(
                                f"Failed to execute scheduled workflow {workflow_id}: {e}"
                            )

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)

    def get_workflow_execution(
        self, workflow_id: str, execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get workflow execution details."""
        if workflow_id not in self.workflows:
            return None

        for execution in self.workflows[workflow_id]["executions"]:
            if execution["id"] == execution_id:
                return dict(execution)

        return None

    def get_workflow_executions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all executions for a workflow."""
        if workflow_id not in self.workflows:
            return []

        return [
            dict(execution) for execution in self.workflows[workflow_id]["executions"]
        ]

    def is_healthy(self) -> bool:
        """Check if Temporal service is healthy."""
        return self.running

    def get_metrics(self) -> Dict[str, Any]:
        """Get Temporal service metrics."""
        total_executions = sum(len(wf["executions"]) for wf in self.workflows.values())
        running_executions = sum(
            1
            for wf in self.workflows.values()
            for exec in wf["executions"]
            if exec["status"] == "RUNNING"
        )

        return {
            "running": self.running,
            "registered_workflows": len(self.workflows),
            "scheduled_workflows": len(self.scheduled_workflows),
            "total_executions": total_executions,
            "running_executions": running_executions,
            "registered_activities": len(self.activities),
        }


# Global Temporal service instance
temporal_service = TemporalService()
