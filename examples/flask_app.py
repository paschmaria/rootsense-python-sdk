"""Flask application example with RootSense integration."""

import os
import time
from flask import Flask, request, jsonify
import rootsense
from rootsense.integrations.flask import capture_flask_errors

# Initialize RootSense
rootsense.init(
    api_key=os.getenv("ROOTSENSE_API_KEY", "test_api_key"),
    project_id=os.getenv("ROOTSENSE_PROJECT_ID", "test_project_id"),
    environment="development",
    debug=True
)

app = Flask(__name__)

# Add RootSense middleware
capture_flask_errors(app)


@app.route("/")
def index():
    return jsonify({
        "message": "Flask app with RootSense integration",
        "status": "healthy"
    })


@app.route("/api/users/<int:user_id>")
def get_user(user_id):
    """Get user by ID - demonstrates successful request tracking."""
    return jsonify({
        "id": user_id,
        "username": f"user_{user_id}",
        "email": f"user{user_id}@example.com"
    })


@app.route("/api/error")
def trigger_error():
    """Trigger an error - demonstrates error capture."""
    raise ValueError("This is a test error!")


@app.route("/api/slow")
def slow_endpoint():
    """Slow endpoint - demonstrates performance monitoring."""
    time.sleep(2)  # Simulate slow operation
    return jsonify({"message": "Slow operation completed"})


@app.route("/api/database")
def database_query():
    """Simulates database query - demonstrates database monitoring."""
    from rootsense.performance import DatabaseMonitor
    
    db_monitor = DatabaseMonitor()
    
    with db_monitor.track_query(
        "SELECT * FROM users WHERE active = true",
        operation="SELECT",
        database="main"
    ):
        time.sleep(0.5)  # Simulate query time
    
    return jsonify({
        "message": "Database query completed",
        "stats": db_monitor.get_stats()
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
