"""
Django views example with RootSense integration.

Add these views to your Django project's urls.py:

    from . import views
    
    urlpatterns = [
        path('', views.index, name='index'),
        path('error/', views.trigger_error, name='error'),
        path('user/<str:user_id>/', views.user_profile, name='user_profile'),
        path('slow/', views.slow_view, name='slow'),
    ]
"""

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import rootsense
import time
import random


def index(request):
    """Home page."""
    return JsonResponse({
        "message": "Welcome to RootSense Django Demo",
        "endpoints": [
            "/",
            "/error/",
            "/user/<user_id>/",
            "/slow/",
            "/payment/"
        ]
    })


def trigger_error(request):
    """Deliberately trigger an error."""
    rootsense.push_breadcrumb(
        message="User requested /error/ endpoint",
        category="navigation",
        level="info"
    )
    
    rootsense.set_tag("error_type", "deliberate")
    
    # This will be automatically captured by RootSense middleware
    raise ValueError("This is a deliberate error for testing!")


def user_profile(request, user_id):
    """User-specific view."""
    # Set user context
    rootsense.set_user(
        id=user_id,
        username=f"user_{user_id}",
        email=f"user{user_id}@example.com"
    )
    
    # Add tags
    user_num = int(user_id) if user_id.isdigit() else 0
    rootsense.set_tag("user_type", "premium" if user_num % 2 == 0 else "free")
    
    # Simulate errors for some users
    if user_num % 5 == 0:
        rootsense.push_breadcrumb(
            message=f"Loading profile for user {user_id}",
            category="database",
            level="info"
        )
        raise RuntimeError(f"Failed to load profile for user {user_id}")
    
    return JsonResponse({
        "user_id": user_id,
        "username": f"user_{user_id}",
        "status": "active",
        "plan": "premium" if user_num % 2 == 0 else "free"
    })


def slow_view(request):
    """View with deliberate slowness."""
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
    
    return JsonResponse({
        "message": "Slow operation completed",
        "duration": duration
    })


@csrf_exempt
@require_http_methods(["POST"])
def payment_view(request):
    """Payment processing view."""
    import json
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    
    amount = data.get("amount", 0)
    
    # Add payment context
    rootsense.set_context("payment", {
        "amount": amount,
        "currency": data.get("currency", "USD"),
        "method": data.get("method", "credit_card")
    })
    
    rootsense.push_breadcrumb(
        message="Payment processing started",
        category="payment",
        level="info",
        data={"amount": amount}
    )
    
    # Validate
    if amount <= 0:
        rootsense.push_breadcrumb(
            message="Invalid payment amount",
            category="validation",
            level="error"
        )
        raise ValueError(f"Invalid payment amount: {amount}")
    
    if amount > 10000:
        raise ValueError("Payment amount exceeds limit")
    
    # Simulate processing
    time.sleep(random.uniform(0.1, 0.5))
    
    # Random failures
    if random.random() < 0.1:
        rootsense.push_breadcrumb(
            message="Payment gateway error",
            category="payment",
            level="error"
        )
        raise RuntimeError("Payment gateway connection failed")
    
    return JsonResponse({
        "status": "success",
        "transaction_id": f"txn_{int(time.time())}",
        "amount": amount
    })


def database_error(request):
    """Simulate database error."""
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
    
    raise ConnectionError("Database connection pool exhausted")


def nested_error(request):
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
