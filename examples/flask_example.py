"""Flask integration example with auto-instrumentation.

This example shows how to use RootSense with Flask.
All database queries, HTTP requests, and errors are captured automatically!
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import rootsense
import os

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/myapp'
db = SQLAlchemy(app)

# Initialize RootSense (do this AFTER creating app)
rootsense.init(
    api_key=os.getenv("ROOTSENSE_API_KEY"),
    project_id=os.getenv("ROOTSENSE_PROJECT_ID"),
    environment=os.getenv("ENVIRONMENT", "production"),
    service_name="my-flask-app",
    service_version="1.0.0",
    enable_auto_instrumentation=True  # Default: True
)

# That's it! Flask is now fully instrumented:
# - HTTP requests: auto-tracked
# - SQLAlchemy queries: auto-tracked
# - External HTTP calls: auto-tracked
# - Errors: auto-captured
# - Auto-resolution: enabled

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name
        }

# Routes
@app.route('/api/users')
def list_users():
    """List all users.
    
    This SQLAlchemy query is automatically tracked!
    - Query text captured
    - Execution time measured
    - Database name recorded
    - If fails: incident created
    - When succeeds again: incident auto-resolved
    """
    users = User.query.all()
    return jsonify({
        "users": [u.to_dict() for u in users]
    })

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    """Get user by ID.
    
    Automatically tracked with auto-resolution!
    """
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user.
    
    Database INSERT automatically tracked!
    """
    data = request.get_json()
    
    # This database operation is automatically tracked
    user = User(
        email=data['email'],
        name=data['name']
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@app.route('/api/external-data')
def fetch_external_data():
    """Fetch data from external API.
    
    HTTP request is automatically tracked!
    """
    import requests
    
    # This HTTP request is automatically tracked by OpenTelemetry!
    # - URL, method, status code
    # - Response time
    # - If fails: incident created
    # - When succeeds: incident resolved
    response = requests.get('https://api.example.com/data')
    response.raise_for_status()
    
    return jsonify(response.json())

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler.
    
    All errors are automatically captured by RootSense!
    This handler is optional - just for custom responses.
    """
    return jsonify({
        "error": str(error)
    }), 500

if __name__ == '__main__':
    app.run(debug=True)

# What gets tracked automatically:
# --------------------------------
# 1. HTTP Requests:
#    - GET /api/users
#    - POST /api/users
#    - GET /api/users/123
#    - All with timing and status codes
#
# 2. Database Queries:
#    - User.query.all()
#    - User.query.get(123)
#    - db.session.add() / commit()
#    - All with execution time
#
# 3. External HTTP Calls:
#    - requests.get()
#    - requests.post()
#    - With full request/response tracking
#
# 4. Errors:
#    - All unhandled exceptions
#    - With stack traces
#    - With request context
#
# 5. Auto-Resolution:
#    - Automatic when operations recover
#    - No manual intervention needed
