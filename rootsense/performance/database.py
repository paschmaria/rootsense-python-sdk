"""Database performance monitoring."""

import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from rootsense.context import push_breadcrumb, set_tag

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Monitor database query performance."""

    def __init__(self):
        self.query_count = 0
        self.total_time = 0.0
        self.slow_query_threshold = 0.5  # 500ms

    @contextmanager
    def track_query(
        self,
        query: str,
        operation: str = "SELECT",
        database: Optional[str] = None,
        **kwargs
    ):
        """Track a database query.
        
        Args:
            query: SQL query string
            operation: Type of operation (SELECT, INSERT, UPDATE, DELETE)
            database: Database name
            **kwargs: Additional metadata
            
        Example:
            >>> monitor = DatabaseMonitor()
            >>> with monitor.track_query(
            ...     "SELECT * FROM users WHERE id = %s",
            ...     operation="SELECT",
            ...     database="main"
            ... ):
            ...     # Execute query
            ...     pass
        """
        start_time = time.time()
        self.query_count += 1
        
        # Truncate long queries for logging
        truncated_query = query[:200] + "..." if len(query) > 200 else query
        
        push_breadcrumb(
            category="database",
            message=f"Database query started: {operation}",
            level="info",
            data={
                "query": truncated_query,
                "operation": operation,
                "database": database,
                **kwargs
            }
        )
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.total_time += duration
            
            # Record metrics
            set_tag("database.query_count", self.query_count)
            set_tag("database.total_time", self.total_time)
            set_tag("database.last_query_duration", duration)
            
            # Record slow queries
            if duration > self.slow_query_threshold:
                logger.warning(
                    f"Slow database query detected: {operation} took {duration:.2f}s",
                    extra={
                        "query": truncated_query,
                        "duration": duration,
                        "operation": operation,
                        "database": database,
                        **kwargs
                    }
                )
                
                push_breadcrumb(
                    category="database",
                    message=f"Slow query: {operation}",
                    level="warning",
                    data={
                        "query": truncated_query,
                        "duration": duration,
                        "operation": operation,
                        "database": database,
                    }
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get database performance statistics.
        
        Returns:
            Dictionary with performance stats
        """
        avg_time = self.total_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "query_count": self.query_count,
            "total_time": self.total_time,
            "average_time": avg_time,
        }

    def reset_stats(self):
        """Reset performance statistics."""
        self.query_count = 0
        self.total_time = 0.0
