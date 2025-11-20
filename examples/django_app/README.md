# Django Example Application with RootSense Integration

This is a minimal Django application demonstrating RootSense integration.

## Installation

```bash
pip install rootsense[django]
```

## Setup

1. Create a Django project (if you don't have one):
```bash
django-admin startproject myproject
cd myproject
```

2. Copy the files from this directory to your Django project

3. Update your `settings.py` with the configuration shown in `settings.py`

4. Run migrations:
```bash
python manage.py migrate
```

5. Run the development server:
```bash
python manage.py runserver
```

## Test Endpoints

- http://localhost:8000/ - Home page
- http://localhost:8000/error/ - Trigger error
- http://localhost:8000/user/123/ - User-specific page
- http://localhost:8000/slow/ - Slow endpoint
- http://localhost:8000/admin/ - Django admin

## Files

- `settings.py` - Django settings with RootSense configuration
- `urls.py` - URL configuration
- `views.py` - View functions with RootSense examples

## RootSense Configuration

RootSense is configured in `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware
    'rootsense.integrations.django.RootSenseDjangoMiddleware',
]

ROOTSENSE = {
    'api_key': 'your-api-key',
    'project_id': 'your-project-id',
    'environment': 'production',
    'send_default_pii': False,
    'enable_prometheus': True,
    'debug': True,
}
```

The middleware automatically:
- Captures all unhandled exceptions
- Adds Django request context
- Tracks user information (if authenticated)
- Collects performance metrics
