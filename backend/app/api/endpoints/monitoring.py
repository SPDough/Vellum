"""
Monitoring and performance endpoints for Otomeshon Banking Platform
"""

import os
import time
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.core.performance import (
    MemoryMonitor,
    cache_manager,
    connection_pool_monitor,
    db_performance_monitor,
    performance_monitor,
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "otomeshon-api",
        "version": "1.0.0",
        "environment": get_settings().environment,
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get comprehensive application metrics"""

    # Performance metrics
    performance_summary = performance_monitor.get_performance_summary()

    # Memory metrics
    memory_stats = MemoryMonitor.get_memory_stats()

    # Cache metrics
    cache_stats = cache_manager.get_stats()

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "performance": performance_summary,
        "memory": memory_stats,
        "cache": cache_stats,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        },
        "database": {
            "total_queries": db_performance_monitor.query_count,
            "avg_query_time_ms": (
                db_performance_monitor.total_query_time
                / db_performance_monitor.query_count
                if db_performance_monitor.query_count > 0
                else 0
            ),
            "slow_queries_count": len(db_performance_monitor.slow_queries),
        },
    }


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get detailed performance metrics"""
    return performance_monitor.get_performance_summary()


@router.get("/database")
async def get_database_metrics() -> Dict[str, Any]:
    """Get database performance metrics"""
    return {
        "query_count": db_performance_monitor.query_count,
        "total_query_time_ms": db_performance_monitor.total_query_time,
        "average_query_time_ms": (
            db_performance_monitor.total_query_time / db_performance_monitor.query_count
            if db_performance_monitor.query_count > 0
            else 0
        ),
        "slow_queries": [
            {
                "statement": q["statement"][:200],  # Truncate for security
                "duration_ms": q["duration_ms"],
                "timestamp": q["timestamp"].isoformat(),
            }
            for q in db_performance_monitor.slow_queries[-10:]  # Last 10 slow queries
        ],
        "connection_pools": connection_pool_monitor.pool_stats,
    }


@router.get("/memory")
async def get_memory_metrics() -> Dict[str, Any]:
    """Get memory usage metrics"""
    return MemoryMonitor.get_memory_stats()


@router.post("/memory/gc")
async def force_garbage_collection() -> Dict[str, Any]:
    """Force garbage collection (admin endpoint)"""
    gc_stats = MemoryMonitor.force_garbage_collection()

    return {
        "message": "Garbage collection completed",
        "stats": gc_stats,
        "memory_after": MemoryMonitor.get_memory_stats(),
    }


@router.get("/cache")
async def get_cache_metrics() -> Dict[str, Any]:
    """Get cache performance metrics"""
    return cache_manager.get_stats()


@router.delete("/cache")
async def clear_cache() -> Dict[str, Any]:
    """Clear application cache (admin endpoint)"""
    cache_manager.clear()
    return {"message": "Cache cleared successfully"}


@router.get("/alerts")
async def get_performance_alerts() -> Dict[str, Any]:
    """Get performance alerts and warnings"""
    alerts = []
    warnings = []

    # Check response times
    perf_summary = performance_monitor.get_performance_summary()
    if "response_times" in perf_summary:
        avg_response = perf_summary["response_times"]["avg_ms"]
        if avg_response > 1000:  # 1 second
            alerts.append(f"High average response time: {avg_response:.2f}ms")
        elif avg_response > 500:  # 500ms
            warnings.append(f"Elevated average response time: {avg_response:.2f}ms")

    # Check error rate
    error_rate = perf_summary.get("error_rate", 0)
    if error_rate > 0.05:  # 5%
        alerts.append(f"High error rate: {error_rate:.2%}")
    elif error_rate > 0.01:  # 1%
        warnings.append(f"Elevated error rate: {error_rate:.2%}")

    # Check memory usage
    memory_stats = MemoryMonitor.get_memory_stats()
    memory_percent = memory_stats.get("percent", 0)
    if memory_percent > 90:
        alerts.append(f"Critical memory usage: {memory_percent:.1f}%")
    elif memory_percent > 75:
        warnings.append(f"High memory usage: {memory_percent:.1f}%")

    # Check slow queries
    if len(db_performance_monitor.slow_queries) > 10:
        warnings.append(
            f"Multiple slow database queries detected: {len(db_performance_monitor.slow_queries)}"
        )

    return {
        "alerts": alerts,
        "warnings": warnings,
        "alert_count": len(alerts),
        "warning_count": len(warnings),
        "status": "critical" if alerts else "warning" if warnings else "healthy",
    }


@router.get("/banking-metrics")
async def get_banking_specific_metrics() -> Dict[str, Any]:
    """Get banking-specific performance metrics"""

    # Get endpoint-specific metrics for banking operations
    banking_endpoints = [
        "trade_validation",
        "sop_execution",
        "risk_calculation",
        "compliance_check",
        "settlement_processing",
    ]

    banking_metrics = {}
    for endpoint in banking_endpoints:
        if endpoint in performance_monitor.metrics:
            times = performance_monitor.metrics[endpoint]
            banking_metrics[endpoint] = {
                "total_calls": len(times),
                "avg_response_ms": sum(times) / len(times) if times else 0,
                "max_response_ms": max(times) if times else 0,
                "sla_compliance": (
                    sum(1 for t in times if t < 1000) / len(times) if times else 1.0
                ),
            }

    return {
        "banking_operations": banking_metrics,
        "sla_targets": {
            "trade_validation": "< 100ms",
            "sop_execution": "< 5000ms",
            "risk_calculation": "< 200ms",
            "compliance_check": "< 500ms",
            "settlement_processing": "< 10000ms",
        },
        "regulatory_requirements": {
            "uptime_target": "99.9%",
            "data_retention": "7 years",
            "audit_trail": "complete",
            "disaster_recovery": "< 4 hours RTO",
        },
    }


@router.get("/prometheus")
async def prometheus_metrics() -> str:
    """Export metrics in Prometheus format"""
    perf_summary = performance_monitor.get_performance_summary()
    memory_stats = MemoryMonitor.get_memory_stats()

    metrics = []

    # Response time metrics
    if "response_times" in perf_summary:
        rt = perf_summary["response_times"]
        metrics.extend(
            [
                f"otomeshon_response_time_avg_ms {rt['avg_ms']:.2f}",
                f"otomeshon_response_time_p95_ms {rt['p95_ms']:.2f}",
                f"otomeshon_response_time_p99_ms {rt['p99_ms']:.2f}",
            ]
        )

    # Request metrics
    metrics.extend(
        [
            f"otomeshon_requests_total {perf_summary['total_requests']}",
            f"otomeshon_errors_total {perf_summary['total_errors']}",
            f"otomeshon_requests_per_second {perf_summary['requests_per_second']:.2f}",
            f"otomeshon_error_rate {perf_summary['error_rate']:.4f}",
        ]
    )

    # Memory metrics
    metrics.extend(
        [
            f"otomeshon_memory_rss_mb {memory_stats['rss_mb']:.2f}",
            f"otomeshon_memory_percent {memory_stats['percent']:.2f}",
        ]
    )

    # Database metrics
    metrics.extend(
        [
            f"otomeshon_db_queries_total {db_performance_monitor.query_count}",
            f"otomeshon_db_slow_queries_total {len(db_performance_monitor.slow_queries)}",
        ]
    )

    # Cache metrics
    cache_stats = cache_manager.get_stats()
    metrics.extend(
        [
            f"otomeshon_cache_keys_total {cache_stats['total_keys']}",
            f"otomeshon_cache_memory_mb {cache_stats['memory_estimate_mb']:.2f}",
        ]
    )

    return "\n".join(metrics) + "\n"
