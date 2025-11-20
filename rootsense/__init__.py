"""RootSense Python SDK - AI-powered incident management and error tracking."""

from rootsense.client import RootSenseClient
from rootsense.config import init, get_client
from rootsense.context import push_breadcrumb, set_context, set_tag, set_user

__version__ = "0.1.0"
__all__ = [
    "init",
    "get_client",
    "push_breadcrumb",
    "set_context",
    "set_tag",
    "set_user",
    "RootSenseClient",
]
