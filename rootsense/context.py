"""Context management for enriching events."""

import threading
from collections import deque
from typing import Any, Dict, Optional


class Context:
    """Thread-local context for events."""

    def __init__(self, max_breadcrumbs: int = 100):
        self.max_breadcrumbs = max_breadcrumbs
        self._local = threading.local()

    def _get_context(self) -> Dict[str, Any]:
        """Get thread-local context."""
        if not hasattr(self._local, 'context'):
            self._local.context = {
                'tags': {},
                'extra': {},
                'user': {},
                'breadcrumbs': deque(maxlen=self.max_breadcrumbs)
            }
        return self._local.context

    def set_tag(self, key: str, value: Any):
        """Set a tag."""
        context = self._get_context()
        context['tags'][key] = value

    def set_context(self, key: str, value: Any):
        """Set extra context."""
        context = self._get_context()
        context['extra'][key] = value

    def set_user(self, user_id: Optional[str] = None, email: Optional[str] = None, **kwargs):
        """Set user information."""
        context = self._get_context()
        user_data = {'id': user_id, 'email': email}
        user_data.update(kwargs)
        context['user'] = {k: v for k, v in user_data.items() if v is not None}

    def push_breadcrumb(self, message: str, category: str = "default", level: str = "info", **data):
        """Add a breadcrumb."""
        from datetime import datetime
       
        context = self._get_context()
        breadcrumb = {
            'message': message,
            'category': category,
            'level': level,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        context['breadcrumbs'].append(breadcrumb)

    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        context = self._get_context()
        return {
            'tags': context['tags'].copy(),
            'extra': context['extra'].copy(),
            'user': context['user'].copy(),
            'breadcrumbs': list(context['breadcrumbs'])
        }

    def clear(self):
        """Clear current context."""
        if hasattr(self._local, 'context'):
            del self._local.context


# Global context instance
_context = Context()


def set_tag(key: str, value: Any):
    """Set a tag on the current context."""
    _context.set_tag(key, value)


def set_context(key: str, value: Any):
    """Set extra context."""
    _context.set_context(key, value)


def set_user(user_id: Optional[str] = None, email: Optional[str] = None, **kwargs):
    """Set user information."""
    _context.set_user(user_id, email, **kwargs)


def push_breadcrumb(message: str, category: str = "default", level: str = "info", **data):
    """Add a breadcrumb."""
    _context.push_breadcrumb(message, category, level, **data)


def get_context() -> Dict[str, Any]:
    """Get current context."""
    return _context.get_context()


def clear_context():
    """Clear current context."""
    _context.clear()
