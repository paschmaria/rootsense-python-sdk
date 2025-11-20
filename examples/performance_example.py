"""Performance monitoring examples."""

import time
import rootsense
from rootsense.performance import PerformanceMonitor, track_performance, DatabaseMonitor

# Initialize RootSense
rootsense.init(
    api_key="test_api_key",
    project_id="test_project_id",
    environment="development",
    debug=True
)

monitor = PerformanceMonitor()


def example_context_manager():
    """Example using context manager for performance tracking."""
    print("\n=== Context Manager Example ===")
    
    with monitor.track("api_call", endpoint="/api/users", method="GET"):
        # Simulate API call
        time.sleep(0.5)
        print("API call completed")
    
    with monitor.track("data_processing", records=1000):
        # Simulate data processing
        time.sleep(0.3)
        print("Data processing completed")


@track_performance("user_service.authenticate", service="auth")
def authenticate_user(username: str, password: str):
    """Example using decorator for performance tracking."""
    time.sleep(0.2)  # Simulate authentication
    return {"user_id": 123, "authenticated": True}


def example_decorator():
    """Example using decorator for performance tracking."""
    print("\n=== Decorator Example ===")
    
    result = authenticate_user("john_doe", "password123")
    print(f"Authentication result: {result}")


def example_database_monitoring():
    """Example of database query monitoring."""
    print("\n=== Database Monitoring Example ===")
    
    db_monitor = DatabaseMonitor()
    
    # Track multiple queries
    queries = [
        ("SELECT * FROM users WHERE id = %s", "SELECT"),
        ("INSERT INTO logs (message, timestamp) VALUES (%s, %s)", "INSERT"),
        ("UPDATE users SET last_login = NOW() WHERE id = %s", "UPDATE"),
    ]
    
    for query, operation in queries:
        with db_monitor.track_query(query, operation=operation, database="main"):
            # Simulate query execution
            time.sleep(0.1)
    
    # Get and display statistics
    stats = db_monitor.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Total queries: {stats['query_count']}")
    print(f"  Total time: {stats['total_time']:.2f}s")
    print(f"  Average time: {stats['average_time']:.2f}s")


def example_slow_operation_detection():
    """Example demonstrating slow operation detection."""
    print("\n=== Slow Operation Detection ===")
    
    # This will trigger a slow operation warning (>1 second)
    with monitor.track("slow_computation", complexity="high"):
        time.sleep(1.5)
        print("Slow computation completed")


if __name__ == "__main__":
    print("RootSense Performance Monitoring Examples")
    print("==========================================")
    
    example_context_manager()
    example_decorator()
    example_database_monitoring()
    example_slow_operation_detection()
    
    print("\nExamples completed!")
