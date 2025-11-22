"""Complete example showing all RootSense features."""

import time
import rootsense
from rootsense.context import set_user, set_tag, add_breadcrumb, set_context
from rootsense.performance import PerformanceMonitor, DatabaseMonitor

# Initialize RootSense
rootsense.init(
    connection_string="rootsense://your-api-key@api.rootsense.ai/your-project-id",
    environment="production",
    debug=True,
    sanitize_pii=True
)

# Set user context
set_user({
    "id": "user-123",
    "email": "john@example.com",
    "username": "john_doe"
})

# Add tags
set_tag("environment", "production")
set_tag("version", "1.0.0")
set_tag("region", "us-east-1")

# Performance monitoring
monitor = PerformanceMonitor()

def simulate_database_query():
    """Simulate a database query."""
    db_monitor = DatabaseMonitor()
    
    with db_monitor.track_query(
        "SELECT * FROM users WHERE id = %s",
        operation="SELECT",
        database="main"
    ):
        time.sleep(0.05)  # Simulate query time
        add_breadcrumb("database", "Queried users table")

def simulate_api_call():
    """Simulate an external API call."""
    with monitor.track("external_api", service="payment_gateway"):
        time.sleep(0.1)  # Simulate API latency
        add_breadcrumb("http", "Called payment API", {"endpoint": "/charge"})

def simulate_payment_processing():
    """Simulate payment processing."""
    set_context("payment", {
        "amount": 99.99,
        "currency": "USD",
        "method": "credit_card"
    })
    
    add_breadcrumb("business", "Processing payment", {"amount": 99.99})
    
    try:
        # Simulate operations
        simulate_database_query()
        simulate_api_call()
        
        # Success
        add_breadcrumb("business", "Payment successful")
        rootsense.capture_message("Payment processed successfully", level="info")
        
    except Exception as e:
        # Error
        rootsense.capture_exception(e, context={
            "service": "payment",
            "operation": "process_payment"
        })

def simulate_error():
    """Simulate an error scenario."""
    add_breadcrumb("navigation", "User initiated withdrawal")
    
    try:
        # Simulate error
        amount = 1000
        balance = 500
        
        if amount > balance:
            raise ValueError(f"Insufficient funds: requested {amount}, balance {balance}")
            
    except Exception as e:
        rootsense.capture_exception(e, context={
            "service": "banking",
            "operation": "withdraw",
            "amount": amount,
            "balance": balance
        })

if __name__ == "__main__":
    print("Running RootSense example...")
    
    # Successful operation
    print("\n1. Simulating successful payment...")
    simulate_payment_processing()
    
    # Error scenario
    print("\n2. Simulating error scenario...")
    simulate_error()
    
    # Flush and close
    print("\n3. Flushing events...")
    client = rootsense.get_client()
    if client:
        client.close()
    
    print("\nDone! Check your RootSense dashboard for events.")
