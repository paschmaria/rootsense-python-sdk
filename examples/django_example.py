"""Django integration example with auto-instrumentation.

This example shows how to use RootSense with Django.
All database queries, HTTP requests, and errors are captured automatically!
"""

# settings.py
import rootsense
import os

# Initialize RootSense at Django startup
rootsense.init(
    api_key=os.getenv("ROOTSENSE_API_KEY"),
    project_id=os.getenv("ROOTSENSE_PROJECT_ID"),
    environment=os.getenv("ENVIRONMENT", "production"),
    service_name="my-django-app",
    service_version="1.0.0",
    enable_auto_instrumentation=True  # Default: True
)

# That's it! No middleware needed.
# Django is now fully instrumented:
# - HTTP requests: auto-tracked
# - ORM queries: auto-tracked  
# - Template rendering: auto-tracked
# - Errors: auto-captured
# - Auto-resolution: enabled

# Example views.py
from django.http import JsonResponse
from django.views import View
from .models import User

class UserListView(View):
    def get(self, request):
        # This ORM query is automatically tracked!
        # If it fails: incident created
        # When it succeeds again: incident auto-resolved
        users = User.objects.all()
        
        return JsonResponse({
            "users": list(users.values())
        })

class UserDetailView(View):
    def get(self, request, user_id):
        try:
            # Automatic tracking:
            # - Query execution time
            # - Query text
            # - Database name
            # - Table name
            user = User.objects.get(id=user_id)
            return JsonResponse(user.to_dict())
        except User.DoesNotExist:
            # This exception is automatically captured!
            # Fingerprint: error:DoesNotExist:users
            raise

# Example models.py
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat()
        }

# What gets tracked automatically:
# --------------------------------
# 1. HTTP Requests:
#    - Method, path, status code
#    - Response time
#    - Query parameters (PII sanitized)
#    - Request headers (sensitive ones filtered)
#
# 2. Database Queries:
#    - User.objects.all()
#    - User.objects.filter(email="test@example.com")
#    - User.objects.get(id=123)
#    - All with execution time and query text
#
# 3. Errors:
#    - All unhandled exceptions
#    - With full stack trace
#    - With request context
#    - Auto-fingerprinted for grouping
#
# 4. Auto-Resolution:
#    - When endpoint recovers: incident resolved
#    - When DB queries succeed: incident resolved
#    - Automatic success signal tracking
