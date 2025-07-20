from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4
import random

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

# Request/Response Models
class DataStreamCreate(BaseModel):
    name: str
    data_type: str  # TRADES, POSITIONS, MARKET_DATA, SETTLEMENTS
    source_mcp_server_id: str
    description: Optional[str] = None
    buffer_size: int = 1000
    batch_size: int = 100
    polling_interval_seconds: int = 30

class DataStreamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    buffer_size: Optional[int] = None
    batch_size: Optional[int] = None
    polling_interval_seconds: Optional[int] = None
    enabled: Optional[bool] = None

class DataStreamResponse(BaseModel):
    id: str
    name: str
    data_type: str
    source_mcp_server_id: str
    description: Optional[str]
    status: str  # ACTIVE, PAUSED, ERROR, STOPPED
    buffer_size: int
    batch_size: int
    polling_interval_seconds: int
    records_per_second: float
    latency_ms: int
    subscribers: List[str]
    last_update: datetime
    enabled: bool
    created_at: datetime
    updated_at: datetime

class DataStreamMetrics(BaseModel):
    stream_id: str
    total_records_processed: int
    records_last_hour: int
    records_last_24h: int
    average_latency_ms: float
    error_rate_percentage: float
    uptime_percentage: float
    current_buffer_usage: int
    peak_throughput_rps: float
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

class StreamSubscription(BaseModel):
    subscriber_id: str
    callback_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    filters: dict = {}

# Mock storage
streams_db: dict = {}
subscriptions_db: dict = {}

def generate_mock_metrics() -> dict:
    """Generate realistic mock metrics for data streams."""
    return {
        "records_per_second": round(random.uniform(10, 500), 1),
        "latency_ms": random.randint(50, 300),
        "subscribers": [
            f"workflow-{random.randint(1, 10)}" for _ in range(random.randint(1, 4))
        ]
    }

@router.get("/", response_model=List[DataStreamResponse])
async def list_data_streams(
    data_type: Optional[str] = None,
    status: Optional[str] = None,
    enabled_only: bool = False
):
    """List all data streams."""
    streams = []
    for stream_id, stream_data in streams_db.items():
        if data_type and stream_data.get("data_type") != data_type:
            continue
        if status and stream_data.get("status") != status:
            continue
        if enabled_only and not stream_data.get("enabled", True):
            continue
        
        # Add real-time metrics
        metrics = generate_mock_metrics()
        stream_data.update(metrics)
        stream_data["last_update"] = datetime.utcnow()
        
        streams.append(stream_data)
    
    return streams

@router.post("/", response_model=DataStreamResponse)
async def create_data_stream(stream_data: DataStreamCreate):
    """Create a new data stream."""
    stream_id = str(uuid4())
    
    stream = {
        "id": stream_id,
        "name": stream_data.name,
        "data_type": stream_data.data_type,
        "source_mcp_server_id": stream_data.source_mcp_server_id,
        "description": stream_data.description,
        "status": "ACTIVE",
        "buffer_size": stream_data.buffer_size,
        "batch_size": stream_data.batch_size,
        "polling_interval_seconds": stream_data.polling_interval_seconds,
        "enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **generate_mock_metrics()
    }
    
    streams_db[stream_id] = stream
    return stream

@router.get("/{stream_id}", response_model=DataStreamResponse)
async def get_data_stream(stream_id: str):
    """Get details of a specific data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    stream_data = streams_db[stream_id].copy()
    
    # Add real-time metrics
    metrics = generate_mock_metrics()
    stream_data.update(metrics)
    stream_data["last_update"] = datetime.utcnow()
    
    return stream_data

@router.put("/{stream_id}", response_model=DataStreamResponse)
async def update_data_stream(stream_id: str, update_data: DataStreamUpdate):
    """Update a data stream configuration."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    stream = streams_db[stream_id]
    
    # Update fields if provided
    if update_data.name is not None:
        stream["name"] = update_data.name
    if update_data.description is not None:
        stream["description"] = update_data.description
    if update_data.buffer_size is not None:
        stream["buffer_size"] = update_data.buffer_size
    if update_data.batch_size is not None:
        stream["batch_size"] = update_data.batch_size
    if update_data.polling_interval_seconds is not None:
        stream["polling_interval_seconds"] = update_data.polling_interval_seconds
    if update_data.enabled is not None:
        stream["enabled"] = update_data.enabled
        stream["status"] = "ACTIVE" if update_data.enabled else "PAUSED"
    
    stream["updated_at"] = datetime.utcnow()
    
    return stream

@router.delete("/{stream_id}")
async def delete_data_stream(stream_id: str):
    """Delete a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    del streams_db[stream_id]
    return {"message": "Data stream deleted successfully"}

@router.post("/{stream_id}/start")
async def start_data_stream(stream_id: str):
    """Start a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    stream = streams_db[stream_id]
    stream["status"] = "ACTIVE"
    stream["enabled"] = True
    stream["updated_at"] = datetime.utcnow()
    
    return {"message": "Data stream started successfully"}

@router.post("/{stream_id}/pause")
async def pause_data_stream(stream_id: str):
    """Pause a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    stream = streams_db[stream_id]
    stream["status"] = "PAUSED"
    stream["updated_at"] = datetime.utcnow()
    
    return {"message": "Data stream paused successfully"}

@router.post("/{stream_id}/stop")
async def stop_data_stream(stream_id: str):
    """Stop a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    stream = streams_db[stream_id]
    stream["status"] = "STOPPED"
    stream["enabled"] = False
    stream["updated_at"] = datetime.utcnow()
    
    return {"message": "Data stream stopped successfully"}

@router.get("/{stream_id}/metrics", response_model=DataStreamMetrics)
async def get_stream_metrics(stream_id: str):
    """Get detailed metrics for a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    # Generate realistic metrics
    now = datetime.utcnow()
    
    metrics = {
        "stream_id": stream_id,
        "total_records_processed": random.randint(50000, 1000000),
        "records_last_hour": random.randint(1000, 10000),
        "records_last_24h": random.randint(20000, 200000),
        "average_latency_ms": round(random.uniform(50, 300), 1),
        "error_rate_percentage": round(random.uniform(0, 5), 2),
        "uptime_percentage": round(random.uniform(95, 99.9), 1),
        "current_buffer_usage": random.randint(10, 800),
        "peak_throughput_rps": round(random.uniform(100, 1000), 1),
        "last_error": None,
        "last_error_time": None
    }
    
    # Occasionally add an error
    if random.random() < 0.3:
        metrics["last_error"] = "Connection timeout to source MCP server"
        metrics["last_error_time"] = now - timedelta(minutes=random.randint(5, 120))
    
    return metrics

@router.post("/{stream_id}/subscribe")
async def subscribe_to_stream(stream_id: str, subscription: StreamSubscription):
    """Subscribe to a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    subscription_id = str(uuid4())
    subscription_data = {
        "id": subscription_id,
        "stream_id": stream_id,
        "subscriber_id": subscription.subscriber_id,
        "callback_url": subscription.callback_url,
        "webhook_secret": subscription.webhook_secret,
        "filters": subscription.filters,
        "created_at": datetime.utcnow(),
        "active": True
    }
    
    subscriptions_db[subscription_id] = subscription_data
    
    return {
        "subscription_id": subscription_id,
        "message": "Successfully subscribed to data stream"
    }

@router.delete("/{stream_id}/subscribe/{subscription_id}")
async def unsubscribe_from_stream(stream_id: str, subscription_id: str):
    """Unsubscribe from a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    if subscription_id not in subscriptions_db:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription = subscriptions_db[subscription_id]
    if subscription["stream_id"] != stream_id:
        raise HTTPException(status_code=404, detail="Subscription not found for this stream")
    
    del subscriptions_db[subscription_id]
    
    return {"message": "Successfully unsubscribed from data stream"}

@router.get("/{stream_id}/subscribers")
async def list_stream_subscribers(stream_id: str):
    """List all subscribers for a data stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    subscribers = []
    for subscription_id, subscription_data in subscriptions_db.items():
        if subscription_data["stream_id"] == stream_id and subscription_data.get("active", True):
            subscribers.append({
                "subscription_id": subscription_id,
                "subscriber_id": subscription_data["subscriber_id"],
                "callback_url": subscription_data.get("callback_url"),
                "filters": subscription_data.get("filters", {}),
                "created_at": subscription_data["created_at"]
            })
    
    return {"stream_id": stream_id, "subscribers": subscribers}

@router.get("/{stream_id}/data")
async def get_stream_data(
    stream_id: str,
    limit: int = 100,
    offset: int = 0,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Get recent data from a stream."""
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Data stream not found")
    
    # Generate mock data records
    now = datetime.utcnow()
    mock_records = []
    
    for i in range(min(limit, 50)):  # Limit to 50 for demo
        record_time = now - timedelta(seconds=i * 30)
        
        if start_time and record_time < start_time:
            continue
        if end_time and record_time > end_time:
            continue
        
        # Generate mock record based on data type
        stream_data = streams_db[stream_id]
        data_type = stream_data["data_type"]
        
        if data_type == "TRADES":
            record = {
                "id": str(uuid4()),
                "symbol": random.choice(["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]),
                "quantity": random.randint(100, 10000),
                "price": round(random.uniform(100, 300), 2),
                "side": random.choice(["BUY", "SELL"]),
                "timestamp": record_time
            }
        elif data_type == "POSITIONS":
            record = {
                "id": str(uuid4()),
                "account": f"ACC{random.randint(1000, 9999)}",
                "symbol": random.choice(["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]),
                "quantity": random.randint(-5000, 10000),
                "market_value": round(random.uniform(10000, 500000), 2),
                "timestamp": record_time
            }
        elif data_type == "MARKET_DATA":
            record = {
                "id": str(uuid4()),
                "symbol": random.choice(["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]),
                "bid": round(random.uniform(100, 300), 2),
                "ask": round(random.uniform(100, 300), 2),
                "last": round(random.uniform(100, 300), 2),
                "volume": random.randint(1000, 100000),
                "timestamp": record_time
            }
        else:
            record = {
                "id": str(uuid4()),
                "type": data_type,
                "data": {"value": random.randint(1, 1000)},
                "timestamp": record_time
            }
        
        mock_records.append(record)
    
    return {
        "stream_id": stream_id,
        "total_records": len(mock_records),
        "offset": offset,
        "limit": limit,
        "records": mock_records[offset:offset + limit]
    }