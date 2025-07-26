import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time data updates."""

    def __init__(self):
        # Store active connections by data source ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store all connections for broadcasting
        self.all_connections: Set[WebSocket] = set()
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(
        self, websocket: WebSocket, source_id: str = None, user_id: str = None
    ):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.all_connections.add(websocket)

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "source_id": source_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
        }

        # Subscribe to specific data source if provided
        if source_id:
            if source_id not in self.active_connections:
                self.active_connections[source_id] = set()
            self.active_connections[source_id].add(websocket)

            # Send initial connection confirmation
            await self.send_personal_message(
                {
                    "type": "connection_established",
                    "source_id": source_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Connected to data source: {source_id}",
                },
                websocket,
            )

        logger.info(f"WebSocket connected - Source: {source_id}, User: {user_id}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        # Remove from all connections
        self.all_connections.discard(websocket)

        # Remove from data source subscriptions
        metadata = self.connection_metadata.get(websocket, {})
        source_id = metadata.get("source_id")

        if source_id and source_id in self.active_connections:
            self.active_connections[source_id].discard(websocket)
            if not self.active_connections[source_id]:
                del self.active_connections[source_id]

        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected - Source: {source_id}")

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_source(self, source_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections subscribed to a data source."""
        if source_id not in self.active_connections:
            return

        # Add timestamp and source info to message
        message.update(
            {"timestamp": datetime.utcnow().isoformat(), "source_id": source_id}
        )

        disconnected_connections = []

        for connection in self.active_connections[source_id].copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to source {source_id}: {e}")
                disconnected_connections.append(connection)

        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all active connections."""
        message.update({"timestamp": datetime.utcnow().isoformat()})

        disconnected_connections = []

        for connection in self.all_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to all: {e}")
                disconnected_connections.append(connection)

        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

    async def send_data_update(
        self, source_id: str, data: Any, operation: str = "insert"
    ):
        """Send a data update notification to subscribers."""
        message = {
            "type": "data_update",
            "operation": operation,  # insert, update, delete
            "data": data,
            "source_id": source_id,
        }
        await self.broadcast_to_source(source_id, message)

    async def send_schema_update(self, source_id: str, schema: Dict[str, Any]):
        """Send a schema update notification to subscribers."""
        message = {"type": "schema_update", "schema": schema, "source_id": source_id}
        await self.broadcast_to_source(source_id, message)

    async def send_source_status_update(
        self, source_id: str, status: str, details: str = None
    ):
        """Send a data source status update."""
        message = {
            "type": "source_status_update",
            "status": status,
            "details": details,
            "source_id": source_id,
        }
        await self.broadcast_to_source(source_id, message)

    async def send_workflow_update(
        self, workflow_id: str, execution_id: str, status: str, output_data: Any = None
    ):
        """Send a workflow execution update."""
        message = {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": status,
            "output_data": output_data,
        }
        await self.broadcast_to_all(message)

    async def send_mcp_stream_update(self, server_id: str, stream_name: str, data: Any):
        """Send an MCP data stream update."""
        # Create a pseudo source_id for MCP streams
        source_id = f"mcp:{server_id}:{stream_name}"
        message = {
            "type": "mcp_stream_update",
            "server_id": server_id,
            "stream_name": stream_name,
            "data": data,
        }
        await self.broadcast_to_source(source_id, message)

    async def send_agent_result_update(
        self, agent_id: str, execution_id: str, result: Any
    ):
        """Send an agent execution result update."""
        # Create a pseudo source_id for agent results
        source_id = f"agent:{agent_id}"
        message = {
            "type": "agent_result_update",
            "agent_id": agent_id,
            "execution_id": execution_id,
            "result": result,
        }
        await self.broadcast_to_source(source_id, message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        return {
            "total_connections": len(self.all_connections),
            "source_subscriptions": {
                source_id: len(connections)
                for source_id, connections in self.active_connections.items()
            },
            "connection_details": [
                {
                    "source_id": metadata.get("source_id"),
                    "user_id": metadata.get("user_id"),
                    "connected_at": metadata.get("connected_at"),
                }
                for metadata in self.connection_metadata.values()
            ],
        }


# Global connection manager instance
connection_manager = ConnectionManager()


class DataStreamService:
    """Service for handling real-time data streaming."""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def handle_websocket_connection(
        self, websocket: WebSocket, source_id: str = None, user_id: str = None
    ):
        """Handle a new WebSocket connection with message processing."""
        await self.connection_manager.connect(websocket, source_id, user_id)

        try:
            while True:
                # Wait for messages from the client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    await self.handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await self.connection_manager.send_personal_message(
                        {"type": "error", "message": "Invalid JSON format"}, websocket
                    )
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    await self.connection_manager.send_personal_message(
                        {"type": "error", "message": "Error processing message"},
                        websocket,
                    )

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected normally")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connection_manager.disconnect(websocket)

    async def handle_client_message(
        self, websocket: WebSocket, message: Dict[str, Any]
    ):
        """Handle messages received from WebSocket clients."""
        message_type = message.get("type")

        if message_type == "ping":
            await self.connection_manager.send_personal_message(
                {"type": "pong", "timestamp": datetime.utcnow().isoformat()}, websocket
            )

        elif message_type == "subscribe":
            # Handle subscription to additional data sources
            source_id = message.get("source_id")
            if source_id:
                if source_id not in self.connection_manager.active_connections:
                    self.connection_manager.active_connections[source_id] = set()
                self.connection_manager.active_connections[source_id].add(websocket)

                await self.connection_manager.send_personal_message(
                    {"type": "subscription_confirmed", "source_id": source_id},
                    websocket,
                )

        elif message_type == "unsubscribe":
            # Handle unsubscription from data sources
            source_id = message.get("source_id")
            if source_id and source_id in self.connection_manager.active_connections:
                self.connection_manager.active_connections[source_id].discard(websocket)

                await self.connection_manager.send_personal_message(
                    {"type": "unsubscription_confirmed", "source_id": source_id},
                    websocket,
                )

        elif message_type == "get_stats":
            # Send connection statistics
            stats = self.connection_manager.get_connection_stats()
            await self.connection_manager.send_personal_message(
                {"type": "stats_response", "stats": stats}, websocket
            )

        else:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": f"Unknown message type: {message_type}"},
                websocket,
            )

    async def start_heartbeat(self):
        """Start heartbeat task to keep connections alive."""
        while True:
            try:
                await self.connection_manager.broadcast_to_all(
                    {
                        "type": "heartbeat",
                        "connections": len(self.connection_manager.all_connections),
                    }
                )
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(30)


# Global data stream service instance
data_stream_service = DataStreamService(connection_manager)
