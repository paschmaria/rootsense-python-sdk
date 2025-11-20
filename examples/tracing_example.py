"""Distributed tracing examples."""

import time
import rootsense
from rootsense.tracing import get_tracer, trace_function

# Initialize RootSense
rootsense.init(
    api_key="test_api_key",
    project_id="test_project_id",
    environment="development",
    debug=True
)

tracer = get_tracer()


def example_basic_tracing():
    """Example of basic distributed tracing."""
    print("\n=== Basic Tracing Example ===")
    
    trace_id = tracer.start_trace("user_registration")
    print(f"Started trace: {trace_id}")
    
    with tracer.trace("validate_user_data", parent_trace_id=trace_id) as span:
        # Simulate validation
        time.sleep(0.1)
        span.set_tag("valid", True)
        print("User data validated")
    
    with tracer.trace("create_user_account", parent_trace_id=trace_id) as span:
        # Simulate account creation
        time.sleep(0.2)
        span.set_tag("user_id", 123)
        print("User account created")
    
    with tracer.trace("send_welcome_email", parent_trace_id=trace_id) as span:
        # Simulate email sending
        time.sleep(0.15)
        span.set_tag("email_sent", True)
        print("Welcome email sent")


@trace_function("payment_service.process_payment")
def process_payment(amount: float, currency: str):
    """Example using decorator for tracing."""
    time.sleep(0.3)  # Simulate payment processing
    return {"transaction_id": "txn_123", "status": "completed"}


def example_decorator_tracing():
    """Example using decorator for distributed tracing."""
    print("\n=== Decorator Tracing Example ===")
    
    result = process_payment(99.99, "USD")
    print(f"Payment processed: {result}")


def example_nested_spans():
    """Example of nested spans in distributed tracing."""
    print("\n=== Nested Spans Example ===")
    
    with tracer.trace("api_request") as parent_span:
        parent_span.set_tag("endpoint", "/api/users/123")
        
        with tracer.trace("fetch_user_data") as db_span:
            time.sleep(0.1)
            db_span.set_tag("database", "users_db")
            db_span.set_tag("query_type", "SELECT")
            print("  Fetched user data")
        
        with tracer.trace("fetch_user_permissions") as perm_span:
            time.sleep(0.08)
            perm_span.set_tag("database", "permissions_db")
            perm_span.set_tag("permissions_count", 5)
            print("  Fetched permissions")
        
        with tracer.trace("format_response") as format_span:
            time.sleep(0.05)
            format_span.set_tag("format", "json")
            print("  Formatted response")
        
        parent_span.set_tag("status_code", 200)


def example_error_tracing():
    """Example of tracing with error handling."""
    print("\n=== Error Tracing Example ===")
    
    with tracer.trace("risky_operation") as span:
        span.set_tag("risk_level", "high")
        
        try:
            # Simulate an error
            raise ValueError("Something went wrong!")
        except ValueError as e:
            span.set_error(e)
            print(f"  Error captured in span: {e}")
            # Handle error gracefully


def example_microservices_trace():
    """Example simulating a trace across microservices."""
    print("\n=== Microservices Trace Example ===")
    
    # Simulate incoming request with trace ID
    incoming_trace_id = tracer.start_trace("order_processing")
    print(f"Received order request with trace: {incoming_trace_id}")
    
    # Service 1: Order Service
    with tracer.trace("order_service.validate", parent_trace_id=incoming_trace_id) as span:
        span.set_tag("service", "order-service")
        time.sleep(0.1)
        print("  Order validated")
    
    # Service 2: Inventory Service
    with tracer.trace("inventory_service.check", parent_trace_id=incoming_trace_id) as span:
        span.set_tag("service", "inventory-service")
        time.sleep(0.15)
        span.set_tag("items_available", True)
        print("  Inventory checked")
    
    # Service 3: Payment Service
    with tracer.trace("payment_service.charge", parent_trace_id=incoming_trace_id) as span:
        span.set_tag("service", "payment-service")
        time.sleep(0.2)
        span.set_tag("payment_status", "success")
        print("  Payment processed")
    
    # Service 4: Shipping Service
    with tracer.trace("shipping_service.create", parent_trace_id=incoming_trace_id) as span:
        span.set_tag("service", "shipping-service")
        time.sleep(0.12)
        span.set_tag("tracking_number", "TRK123456")
        print("  Shipping label created")


def display_trace_data():
    """Display collected trace data."""
    print("\n=== Trace Data ===")
    
    trace_data = tracer.get_trace_data()
    
    print(f"\nCompleted Spans: {len(trace_data['completed_spans'])}")
    for span in trace_data['completed_spans']:
        print(f"  - {span['operation']}: {span['duration']:.3f}s")


if __name__ == "__main__":
    print("RootSense Distributed Tracing Examples")
    print("=======================================")
    
    example_basic_tracing()
    example_decorator_tracing()
    example_nested_spans()
    example_error_tracing()
    example_microservices_trace()
    display_trace_data()
    
    print("\nExamples completed!")
