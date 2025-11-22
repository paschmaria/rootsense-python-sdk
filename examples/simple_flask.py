"""Simple Flask example with RootSense."""

from flask import Flask, request
import rootsense
from rootsense.middleware.flask import capture_flask_errors
from rootsense.context import set_user, add_breadcrumb

app = Flask(__name__)

# Initialize RootSense
rootsense.init(
    connection_string="rootsense://your-api-key@api.rootsense.ai/your-project-id",
    environment="development",
    debug=True
)

# Add RootSense integration
capture_flask_errors(app)

@app.route("/")
def index():
    return {"message": "Hello from RootSense!"}, 200

@app.route("/user/<user_id>")
def get_user(user_id):
    # Set user context
    set_user({"id": user_id})
    
    add_breadcrumb("api", f"Fetching user {user_id}")
    
    # Simulate user fetch
    return {"id": user_id, "name": "John Doe"}, 200

@app.route("/error")
def trigger_error():
    # This will be automatically captured by RootSense
    raise ValueError("Test error for demonstration")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
