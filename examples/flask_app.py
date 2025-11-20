"""Flask application example with RootSense integration.

This example demonstrates:
- Flask integration using RootSenseFlask
- Automatic error capture from Flask routes
- Custom context per request
- User tracking
- Performance metrics collection

Installation:
    pip install rootsense[flask]

Run:
    python flask_app.py
    
Test endpoints:
    http://localhost:5000/               # Success
    http://localhost:5000/error          # Trigger error
    http://localhost:5000/user/123       # User-specific route
    http://localhost:5000/payment        # Payment processing
"""

from flask import Flask, request, jsonify
import rootsense
from rootsense.integrations.flask import RootSenseFlask
import random
import time


# Create Flask app
app = Flask(__name__)

# Initialize RootSense for Flask
# This automatically:
# - Captures all unhandled exceptions
# - Adds request context (URL, method, headers, etc.)
# - Tracks performance metrics
# - Exposes /metrics endpoint for Prometheus
RootSenseFlask(
    app,
    api_key="your-api-key",  # Replace with your actual API key
    project_id="your-project-id",  # Replace with your project ID
    environment="production",
    send_default_pii=False,
    enable_prometheus=True,
    debug=True
)


@app.route("/")
def index():
    """Home page - no errors."""
    return jsonify({
        "message": "Welcome to RootSense Flask Demo",
        "endpoints": [
            "/",
            "/error",
            "/user/<user_id>",
            "/payment",
            "/slow",
            "/metrics"
        ]
    })


@app.route("/error")
def trigger_error():
    """Endpoint that deliberately throws an error."""
    # Add some context before the error
    rootsense.push_breadcrumb(
        message="User requested /error endpoint",
        category="navigation",
        level="info"
    )
    
    rootsense.set_tag("error_type", "deliberate")
    
    # This will be automatically captured by RootSense
    raise ValueError("This is a deliberate error for testing!")


@app.route("/user/<user_id>")
def user_profile(user_id):
    """User-specific route with user context."""
    # Set user context for this request
    rootsense.set_user(
        id=user_id,
        username=f"user_{user_id}",
        email=f"user{user_id}@example.com"
    )
    
    # Add tags
    rootsense.set_tag("user_type", "premium" if int(user_id) % 2 == 0 else "free")
    
    # Simulate random errors for some users
    if int(user_id) % 5 == 0:
        rootsense.push_breadcrumb(
            message=f"Loading profile for user {user_id}",
            category="database",
            level="info"
        )
        raise RuntimeError(f"Failed to load profile for user {user_id}")
    
    return jsonify({
        "user_id": user_id,
        "username": f"user_{user_id}",
        "status": "active"
    })


@app.route("/payment", methods=["POST"])
def process_payment():
    """Payment processing endpoint."""
    data = request.get_json() or {}
    
    # Add payment context
    rootsense.set_context("payment", {
        "amount": data.get("amount"),
        "currency": data.get("currency", "USD"),
        "method": data.get("method", "credit_card")
    })
    
    rootsense.push_breadcrumb(
        message="Payment processing started",
        category="payment",
        level="info",
        data={"amount": data.get("amount")}
    )
    
    # Validate payment
    amount = data.get("amount", 0)
    if amount <= 0:
        rootsense.push_breadcrumb(
            message="Invalid payment amount",
            category="validation",
            level="error"
        )
        raise ValueError(f"Invalid payment amount: {amount}")
    
    if amount > 10000:
        raise ValueError("Payment amount exceeds limit")
    
    # Simulate payment processing
    time.sleep(random.uniform(0.1, 0.5))
    
    # Random payment failures
    if random.random() < 0.1:  # 10% failure rate
        rootsense.push_breadcrumb(
            message="Payment gateway error",
            category="payment",
            level="error"
        )
        raise RuntimeError("Payment gateway connection failed")
    
    return jsonify({
        "status": "success",
        "transaction_id": f"txn_{int(time.time())}",
        "amount": amount
    })


@app.route("/slow")
def slow_endpoint():
    """Endpoint with deliberate slowness to test performance monitoring."""
    rootsense.push_breadcrumb(
        message="Starting slow operation",
        category="performance",
        level="info"
    )
    
    # Simulate slow operation
    duration = random.uniform(1, 3)
    time.sleep(duration)
    
    rootsense.set_tag("slow_operation", "true")
    rootsense.set_context("performance", {
        "duration_seconds": duration
    })
    
    return jsonify({
        "message": "Slow operation completed",
        "duration": duration
    })


@app.route("/database")
def database_error():
    """Simulate database connection error."""
    rootsense.push_breadcrumb(
        message="Attempting database connection",
        category="database",
        level="info"
    )
    
    rootsense.push_breadcrumb(
        message="Database connection timeout",
        category="database",
        level="error",
        data={"timeout": 30}
    )
    
    # Simulate database error
    raise ConnectionError("Database connection pool exhausted")


@app.route("/nested-error")
def nested_error():
    """Error in nested function calls."""
    def level1():
        rootsense.push_breadcrumb(message="Level 1", category="trace", level="debug")
        return level2()
    
    def level2():
        rootsense.push_breadcrumb(message="Level 2", category="trace", level="debug")
        return level3()
    
    def level3():
        rootsense.push_breadcrumb(message="Level 3 - Error!", category="trace", level="error")
        raise RuntimeError("Error in nested function at level 3")
    
    return level1()


@app.before_request
def before_request_handler():
    """Add custom context before each request."""
    # Add request ID for tracking
    request_id = request.headers.get("X-Request-ID", f"req_{int(time.time())}")
    rootsense.set_tag("request_id", request_id)
    
    # Add custom tags based on request
    if request.user_agent:
        rootsense.set_tag("browser", request.user_agent.browser)
        rootsense.set_tag("platform", request.user_agent.platform)


@app.after_request
def after_request_handler(response):
    """Add response context after each request."""
    rootsense.set_tag("response_status", response.status_code)
    return response


@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler."""
    rootsense.capture_message(
        f"404 Not Found: {request.url}",
        level="warning",
        extra={
            "url": request.url,
            "referrer": request.referrer
        }
    )
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler."""
    # Error is already captured by RootSense middleware
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Starting Flask app with RootSense integration...")
    print("Visit http://localhost:5000 to see available endpoints")
    print("Prometheus metrics available at http://localhost:5000/metrics")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
