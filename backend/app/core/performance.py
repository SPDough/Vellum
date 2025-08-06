"""
Performance optimization and monitoring utilities for Otomeshon Banking Platform
"""

import time
import asyncio
import functools
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import statistics
import gc

import structlog
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = structlog.get_logger(__name__)


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {}
        self.response_times = []
        self.db_query_times = []
        self.api_call_counts = {}
        self.error_counts = {}
        self.start_time = time.time()
    
    def record_response_time(self, endpoint: str, duration_ms: float):
        """Record API response time"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = []
        
        self.metrics[endpoint].append(duration_ms)
        self.response_times.append(duration_ms)
        
        # Keep only last 1000 entries to prevent memory issues
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def record_db_query_time(self, query: str, duration_ms: float):
        """Record database query time"""
        self.db_query_times.append({
            'query': query[:100],  # Truncate long queries
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow()
        })
        
        # Keep only last 500 queries
        if len(self.db_query_times) > 500:
            self.db_query_times = self.db_query_times[-500:]
    
    def increment_api_call_count(self, endpoint: str):
        """Increment API call counter"""
        self.api_call_counts[endpoint] = self.api_call_counts.get(endpoint, 0) + 1
    
    def increment_error_count(self, error_type: str):
        """Increment error counter"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_time = time.time()
        uptime_seconds = current_time - self.start_time
        
        summary = {
            'uptime_seconds': uptime_seconds,
            'uptime_human': str(timedelta(seconds=int(uptime_seconds))),
            'total_requests': sum(self.api_call_counts.values()),
            'total_errors': sum(self.error_counts.values()),
            'requests_per_second': sum(self.api_call_counts.values()) / uptime_seconds if uptime_seconds > 0 else 0,
            'error_rate': sum(self.error_counts.values()) / sum(self.api_call_counts.values()) if self.api_call_counts else 0
        }
        
        # Response time statistics
        if self.response_times:
            summary['response_times'] = {
                'avg_ms': statistics.mean(self.response_times),
                'median_ms': statistics.median(self.response_times),
                'p95_ms': self._percentile(self.response_times, 95),
                'p99_ms': self._percentile(self.response_times, 99),
                'min_ms': min(self.response_times),
                'max_ms': max(self.response_times)
            }
        
        # Database query statistics
        if self.db_query_times:
            query_durations = [q['duration_ms'] for q in self.db_query_times]
            summary['database_queries'] = {
                'total_queries': len(self.db_query_times),
                'avg_duration_ms': statistics.mean(query_durations),
                'median_duration_ms': statistics.median(query_durations),
                'p95_duration_ms': self._percentile(query_durations, 95),
                'slowest_queries': sorted(self.db_query_times, key=lambda x: x['duration_ms'], reverse=True)[:5]
            }
        
        # Top endpoints by call count
        summary['top_endpoints'] = sorted(
            self.api_call_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Error breakdown
        summary['error_breakdown'] = dict(self.error_counts)
        
        return summary
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * len(sorted_data)
        
        if index.is_integer():
            return sorted_data[int(index) - 1]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def performance_timing(func_name: Optional[str] = None):
    """Decorator to measure function execution time"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                name = func_name or f"{func.__module__}.{func.__name__}"
                performance_monitor.record_response_time(name, duration_ms)
                
                if duration_ms > 1000:  # Log slow operations
                    logger.warning(
                        "Slow operation detected",
                        function=name,
                        duration_ms=duration_ms
                    )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                name = func_name or f"{func.__module__}.{func.__name__}"
                performance_monitor.record_response_time(name, duration_ms)
                
                if duration_ms > 1000:  # Log slow operations
                    logger.warning(
                        "Slow operation detected",
                        function=name,
                        duration_ms=duration_ms
                    )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


@asynccontextmanager
async def performance_context(operation_name: str):
    """Context manager for measuring operation performance"""
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        performance_monitor.record_response_time(operation_name, duration_ms)


class DatabasePerformanceMonitor:
    """Monitor database query performance"""
    
    def __init__(self):
        self.query_count = 0
        self.total_query_time = 0
        self.slow_queries = []
    
    def setup_sqlalchemy_monitoring(self, engine: Engine):
        """Setup SQLAlchemy event listeners for query monitoring"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            duration_ms = total * 1000
            
            self.query_count += 1
            self.total_query_time += duration_ms
            
            # Record in performance monitor
            performance_monitor.record_db_query_time(statement, duration_ms)
            
            # Log slow queries (> 100ms)
            if duration_ms > 100:
                self.slow_queries.append({
                    'statement': statement,
                    'duration_ms': duration_ms,
                    'timestamp': datetime.utcnow()
                })
                
                logger.warning(
                    "Slow database query detected",
                    duration_ms=duration_ms,
                    statement=statement[:200]  # Truncate long statements
                )
                
                # Keep only last 100 slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]


class MemoryMonitor:
    """Monitor memory usage and garbage collection"""
    
    @staticmethod
    def get_memory_stats() -> Dict[str, Any]:
        """Get current memory statistics"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'gc_counts': gc.get_count(),
            'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
        }
    
    @staticmethod
    def force_garbage_collection():
        """Force garbage collection and return stats"""
        before_counts = gc.get_count()
        collected = gc.collect()
        after_counts = gc.get_count()
        
        return {
            'objects_collected': collected,
            'before_counts': before_counts,
            'after_counts': after_counts
        }


class CacheManager:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Any] = {}
        self.ttl_map: Dict[str, float] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Check TTL
            if key in self.ttl_map:
                if time.time() > self.ttl_map[key]:
                    # Expired
                    del self.cache[key]
                    del self.ttl_map[key]
                    return None
            
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        self.cache[key] = value
        if ttl is None:
            ttl = self.default_ttl
        
        self.ttl_map[key] = time.time() + ttl
        
        # Simple cleanup - remove expired entries
        self._cleanup_expired()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl_map:
                del self.ttl_map[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.ttl_map.clear()
    
    def _cleanup_expired(self) -> None:
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.ttl_map.items()
            if current_time > expiry
        ]
        
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
            del self.ttl_map[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._cleanup_expired()
        return {
            'total_keys': len(self.cache),
            'memory_estimate_mb': len(str(self.cache)) / 1024 / 1024,
            'hit_rate': getattr(self, '_hit_rate', 0.0)  # Would need to track hits/misses
        }


class ConnectionPoolMonitor:
    """Monitor database connection pool performance"""
    
    def __init__(self):
        self.pool_stats = {}
    
    def record_pool_stats(self, pool_name: str, pool):
        """Record connection pool statistics"""
        try:
            stats = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'timestamp': datetime.utcnow()
            }
            
            self.pool_stats[pool_name] = stats
            
            # Log warnings for pool exhaustion
            if stats['checked_out'] >= stats['size'] * 0.8:  # 80% utilization
                logger.warning(
                    "High database connection pool utilization",
                    pool_name=pool_name,
                    utilization=stats['checked_out'] / stats['size'] * 100
                )
                
        except Exception as e:
            logger.error("Failed to collect pool stats", error=str(e))


# Global instances
db_performance_monitor = DatabasePerformanceMonitor()
cache_manager = CacheManager()
connection_pool_monitor = ConnectionPoolMonitor()


# Performance optimization decorators
def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator to cache function results"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def rate_limit(max_calls: int, time_window: int = 60):
    """Decorator to rate limit function calls"""
    call_times: Dict[str, List[float]] = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            func_key = f"{func.__module__}.{func.__name__}"
            
            if func_key not in call_times:
                call_times[func_key] = []
            
            # Remove old calls outside time window
            call_times[func_key] = [
                t for t in call_times[func_key]
                if current_time - t < time_window
            ]
            
            # Check rate limit
            if len(call_times[func_key]) >= max_calls:
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {time_window}s")
            
            # Record this call
            call_times[func_key].append(current_time)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
