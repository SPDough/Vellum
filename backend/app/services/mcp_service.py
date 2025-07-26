import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx

from app.core.config import get_settings
from app.core.telemetry import business_metrics, get_tracer
from app.models.data import DataFlow, DataStream, MCPServer

logger = logging.getLogger(__name__)
tracer = get_tracer("mcp_service")
settings = get_settings()


class MCPProtocol(str, Enum):
    """MCP Protocol versions supported."""

    V1_0 = "1.0"
    V2_0 = "2.0"


class MCPServerType(str, Enum):
    """Types of MCP servers we integrate with."""

    CUSTODIAN = "custodian"
    MARKET_DATA = "market_data"
    PRICING = "pricing"
    REFERENCE_DATA = "reference_data"
    SETTLEMENT = "settlement"


class MCPClient(ABC):
    """Abstract base class for MCP client implementations."""

    def __init__(self) -> None:
        self.connected: bool = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to MCP server."""
        pass

    @abstractmethod
    async def call_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server."""
        pass

    @abstractmethod
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities."""
        pass


class HTTPMCPClient(MCPClient):
    """HTTP-based MCP client implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__()
        self.base_url = config["base_url"]
        self.auth_type = config.get("auth_type", "none")
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 30)
        self.headers = {"Content-Type": "application/json"}

        if self.auth_type == "api_key" and self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    async def connect(self) -> bool:
        """Test connection to MCP server."""
        try:
            response = await self.client.get("/mcp/info")
            response.raise_for_status()
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.base_url}: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
        self.connected = False

    async def call_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call MCP tool via HTTP."""
        with tracer.start_as_current_span("mcp_tool_call") as span:
            span.set_attributes(
                {
                    "mcp.server": self.base_url,
                    "mcp.tool": tool_name,
                    "mcp.parameters_count": len(parameters),
                }
            )

            try:
                payload = {"tool": tool_name, "parameters": parameters}

                response = await self.client.post("/mcp/tools/call", json=payload)
                response.raise_for_status()

                result = response.json()

                span.set_attributes(
                    {"mcp.success": True, "mcp.response_size": len(str(result))}
                )

                return result

            except Exception as e:
                span.set_attribute("mcp.success", False)
                span.record_exception(e)
                logger.error(f"MCP tool call failed: {e}")
                raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server."""
        try:
            response = await self.client.get("/mcp/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []

    async def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information."""
        try:
            response = await self.client.get("/mcp/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get MCP server info: {e}")
            return {}


class WebSocketMCPClient(MCPClient):
    """WebSocket-based MCP client for real-time data."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__()
        self.ws_url = config["ws_url"]
        self.auth_token = config.get("auth_token")
        self.websocket = None
        self.message_id = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}

    async def connect(self) -> bool:
        """Establish WebSocket connection."""
        try:
            import websockets

            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            self.websocket = await websockets.connect(
                self.ws_url, extra_headers=headers
            )
            self.connected = True

            # Start message handler
            asyncio.create_task(self._handle_messages())
            return True

        except Exception as e:
            logger.error(f"Failed to connect WebSocket MCP: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
        self.connected = False

    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            if not self.websocket:
                return
            async for message in self.websocket:
                data = json.loads(message)

                if "id" in data and data["id"] in self.pending_requests:
                    # Response to our request
                    future = self.pending_requests.pop(data["id"])
                    future.set_result(data)
                else:
                    # Server-initiated message (subscription data, etc.)
                    await self._handle_server_message(data)

        except Exception as e:
            logger.error(f"WebSocket message handler error: {e}")

    async def _handle_server_message(self, message: Dict[str, Any]) -> None:
        """Handle server-initiated messages."""
        # Handle real-time data updates, notifications, etc.
        logger.info(f"Received server message: {message.get('type', 'unknown')}")

    async def call_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call tool via WebSocket."""
        if not self.connected:
            raise RuntimeError("WebSocket not connected")

        self.message_id += 1
        message = {
            "id": self.message_id,
            "type": "tool_call",
            "tool": tool_name,
            "parameters": parameters,
        }

        future: asyncio.Future[Dict[str, Any]] = asyncio.Future()
        self.pending_requests[self.message_id] = future

        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        await self.websocket.send(json.dumps(message))

        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(future, timeout=30)
            return response.get("result", {})
        except asyncio.TimeoutError:
            self.pending_requests.pop(self.message_id, None)
            raise TimeoutError("MCP tool call timed out")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools via WebSocket."""
        result = await self.call_tool("list_tools", {})
        return result.get("tools", [])

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server info via WebSocket."""
        return await self.call_tool("get_info", {})


class MCPServerManager:
    """Manages connections to multiple MCP servers."""

    def __init__(self) -> None:
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.clients: Dict[str, MCPClient] = {}
        self.health_check_interval = 60  # seconds
        self._health_check_task = None

    async def register_server(self, server_config: Dict[str, Any]) -> bool:
        """Register a new MCP server."""
        server_id = server_config["id"]

        try:
            # Create appropriate client based on protocol
            client: MCPClient
            if server_config.get("protocol") == "websocket":
                client = WebSocketMCPClient(server_config)
            else:
                client = HTTPMCPClient(server_config)

            # Test connection
            if await client.connect():
                self.servers[server_id] = server_config
                self.clients[server_id] = client

                logger.info(f"Successfully registered MCP server: {server_id}")
                return True
            else:
                await client.disconnect()
                return False

        except Exception as e:
            logger.error(f"Failed to register MCP server {server_id}: {e}")
            return False

    async def unregister_server(self, server_id: str) -> None:
        """Unregister an MCP server."""
        if server_id in self.clients:
            await self.clients[server_id].disconnect()
            del self.clients[server_id]

        if server_id in self.servers:
            del self.servers[server_id]

    async def call_server_tool(
        self, server_id: str, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on a specific MCP server."""
        if server_id not in self.clients:
            raise ValueError(f"MCP server {server_id} not registered")

        client = self.clients[server_id]

        with tracer.start_as_current_span("mcp_server_call") as span:
            span.set_attributes(
                {"mcp.server_id": server_id, "mcp.tool_name": tool_name}
            )

            try:
                result = await client.call_tool(tool_name, parameters)

                # Record metrics
                business_metrics.record_llm_call(  # Using existing metrics
                    model=f"mcp-{server_id}",
                    provider="mcp",
                    tokens=len(str(parameters)) + len(str(result)),
                    cost=0.0,  # MCP calls typically don't have direct costs
                )

                span.set_attribute("mcp.success", True)
                return result

            except Exception as e:
                span.set_attribute("mcp.success", False)
                span.record_exception(e)
                raise

    async def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """Get status of an MCP server."""
        if server_id not in self.clients:
            return {"status": "not_registered"}

        try:
            client = self.clients[server_id]
            info = await client.get_server_info()

            return {
                "status": "connected" if client.connected else "disconnected",
                "server_info": info,
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }

    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List tools available on all registered servers."""
        all_tools = {}

        for server_id, client in self.clients.items():
            try:
                tools = await client.list_tools()
                all_tools[server_id] = tools
            except Exception as e:
                logger.error(f"Failed to list tools for server {server_id}: {e}")
                all_tools[server_id] = []

        return all_tools

    async def start_health_monitoring(self) -> None:
        """Start periodic health checks of all servers."""
        if self._health_check_task:
            return

        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while True:
            try:
                for server_id in list(self.clients.keys()):
                    status = await self.get_server_status(server_id)

                    if status["status"] == "error":
                        logger.warning(f"MCP server {server_id} health check failed")
                        # Could implement reconnection logic here

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.health_check_interval)


# Global MCP server manager instance
mcp_manager = MCPServerManager()


class MCPService:
    """Service layer for MCP server management."""

    def __init__(self) -> None:
        self.manager = mcp_manager
        # In-memory storage for demo - should be replaced with database
        self.servers_db: Dict[str, Dict[str, Any]] = {}
        self.metrics_db: Dict[str, Dict[str, Any]] = {}

    async def list_servers(
        self, provider_type: Optional[str] = None, enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List all registered MCP servers."""
        servers = []
        for server_id, server_data in self.servers_db.items():
            if provider_type and server_data.get("provider_type") != provider_type:
                continue
            if enabled_only and not server_data.get("enabled", True):
                continue

            # Get current status
            status = await self.manager.get_server_status(server_id)
            server_data.update(status)

            servers.append(server_data)

        return servers

    async def create_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new MCP server."""
        server_id = f"mcp_{len(self.servers_db) + 1}"

        # Prepare server configuration
        server_config = {
            "id": server_id,
            "name": server_data["name"],
            "provider_type": server_data["provider_type"],
            "base_url": server_data["base_url"],
            "auth_type": server_data["auth_type"],
            "auth_config": server_data["auth_config"],
            "capabilities": server_data["capabilities"],
            "description": server_data.get("description"),
            "enabled": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "DISCONNECTED",
        }

        # Add auth configuration to the client config
        client_config = {
            "base_url": server_data["base_url"],
            "auth_type": server_data["auth_type"],
            **server_data["auth_config"],
        }

        # Register with manager
        success = await self.manager.register_server({**client_config, "id": server_id})

        if success:
            server_config["status"] = "CONNECTED"
            self.servers_db[server_id] = server_config
            return server_config
        else:
            raise Exception("Failed to connect to MCP server")

    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific MCP server."""
        if server_id not in self.servers_db:
            return None

        server_data = self.servers_db[server_id].copy()
        status = await self.manager.get_server_status(server_id)
        server_data.update(status)

        return server_data

    async def update_server(
        self, server_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an MCP server configuration."""
        if server_id not in self.servers_db:
            return None

        server_data = self.servers_db[server_id]
        server_data.update(update_data)
        server_data["updated_at"] = datetime.utcnow()

        return server_data

    async def delete_server(self, server_id: str) -> bool:
        """Delete an MCP server."""
        if server_id not in self.servers_db:
            return False

        await self.manager.unregister_server(server_id)
        del self.servers_db[server_id]

        return True

    async def test_server_connection(self, server_id: str) -> Dict[str, Any]:
        """Test connection to an MCP server."""
        start_time = datetime.utcnow()

        try:
            status = await self.manager.get_server_status(server_id)
            capabilities = await self.manager.clients[server_id].list_tools()

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "server_id": server_id,
                "success": status["status"] == "connected",
                "response_time_ms": int(response_time),
                "error_message": status.get("error"),
                "capabilities_discovered": [
                    tool.get("name", "unknown") for tool in capabilities
                ],
                "tested_at": datetime.utcnow(),
            }
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "server_id": server_id,
                "success": False,
                "response_time_ms": int(response_time),
                "error_message": str(e),
                "capabilities_discovered": [],
                "tested_at": datetime.utcnow(),
            }

    async def enable_server(self, server_id: str) -> bool:
        """Enable an MCP server."""
        if server_id not in self.servers_db:
            return False

        self.servers_db[server_id]["enabled"] = True
        return True

    async def disable_server(self, server_id: str) -> bool:
        """Disable an MCP server."""
        if server_id not in self.servers_db:
            return False

        self.servers_db[server_id]["enabled"] = False
        return True

    async def get_server_capabilities(self, server_id: str) -> List[Dict[str, Any]]:
        """Get available tools/capabilities from an MCP server."""
        if server_id not in self.manager.clients:
            raise Exception("MCP server not registered")

        client = self.manager.clients[server_id]
        return await client.list_tools()

    async def get_server_metrics(self, server_id: str) -> Dict[str, Any]:
        """Get performance metrics for an MCP server."""
        # Mock metrics for demo - should be collected from actual usage
        return {
            "server_id": server_id,
            "total_requests": 1250,
            "successful_requests": 1180,
            "failed_requests": 70,
            "average_response_time_ms": 245.5,
            "last_24h_requests": 180,
            "uptime_percentage": 94.4,
        }

    async def call_tool(
        self, server_id: str, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a specific tool on an MCP server."""
        return await self.manager.call_server_tool(server_id, tool_name, parameters)


# Global service instance
_mcp_service = None


async def get_mcp_service() -> MCPService:
    """Dependency injection for MCP service."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service


# Predefined MCP server configurations for common custodian/market data providers
PREDEFINED_MCP_SERVERS = {
    "state_street": {
        "id": "state_street",
        "name": "State Street Global Services",
        "type": MCPServerType.CUSTODIAN,
        "base_url": "https://api.statestreet.com/mcp",
        "auth_type": "api_key",
        "tools": ["get_positions", "get_transactions", "get_cash_balances"],
    },
    "bny_mellon": {
        "id": "bny_mellon",
        "name": "BNY Mellon",
        "type": MCPServerType.CUSTODIAN,
        "base_url": "https://api.bnymellon.com/mcp",
        "auth_type": "oauth",
        "tools": ["positions", "transactions", "corporate_actions"],
    },
    "bloomberg": {
        "id": "bloomberg",
        "name": "Bloomberg Market Data",
        "type": MCPServerType.MARKET_DATA,
        "protocol": "websocket",
        "ws_url": "wss://api.bloomberg.com/mcp",
        "tools": ["market_prices", "historical_data", "reference_data"],
    },
    "refinitiv": {
        "id": "refinitiv",
        "name": "Refinitiv Eikon",
        "type": MCPServerType.MARKET_DATA,
        "base_url": "https://api.refinitiv.com/mcp",
        "auth_type": "oauth",
        "tools": ["real_time_prices", "fundamentals", "estimates"],
    },
}
