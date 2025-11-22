"""Automatic instrumentation using OpenTelemetry.

This module provides auto-instrumentation for:
- Django ORM database queries
- Flask/Django HTTP requests  
- SQLAlchemy database queries
- HTTP requests (requests, httpx, urllib)
- Redis operations
- Celery tasks

These instrumentations are leveraged from OpenTelemetry's ecosystem.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Track whether instrumentation is installed
_instrumentation_installed = False


def install_auto_instrumentation(enable_django: bool = True,
                                 enable_flask: bool = True,
                                 enable_sqlalchemy: bool = True,
                                 enable_requests: bool = True,
                                 enable_redis: bool = True,
                                 enable_celery: bool = True) -> bool:
    """Install automatic instrumentation for supported libraries.
    
    This function attempts to install OpenTelemetry instrumentation for
    various popular Python libraries. It will only install instrumentation
    for libraries that are actually installed in the environment.
    
    Args:
        enable_django: Install Django instrumentation (ORM, middleware, views)
        enable_flask: Install Flask instrumentation
        enable_sqlalchemy: Install SQLAlchemy instrumentation
        enable_requests: Install requests/httpx/urllib instrumentation
        enable_redis: Install Redis instrumentation
        enable_celery: Install Celery instrumentation
        
    Returns:
        True if any instrumentation was installed, False otherwise
        
    Example:
        >>> import rootsense
        >>> rootsense.init(api_key="key", project_id="proj")
        >>> # Auto-instrument everything
        >>> from rootsense.instrumentation import install_auto_instrumentation
        >>> install_auto_instrumentation()
    """
    global _instrumentation_installed
    
    if _instrumentation_installed:
        logger.debug("Auto-instrumentation already installed")
        return True
    
    installed_count = 0
    
    # Django instrumentation
    if enable_django:
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            DjangoInstrumentor().instrument()
            logger.info("Installed Django auto-instrumentation (ORM queries, views, middleware)")
            installed_count += 1
        except ImportError:
            logger.debug("Django not installed, skipping Django instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install Django instrumentation: {e}")
    
    # Flask instrumentation
    if enable_flask:
        try:
            from opentelemetry.instrumentation.flask import FlaskInstrumentor
            FlaskInstrumentor().instrument()
            logger.info("Installed Flask auto-instrumentation")
            installed_count += 1
        except ImportError:
            logger.debug("Flask not installed, skipping Flask instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install Flask instrumentation: {e}")
    
    # SQLAlchemy instrumentation
    if enable_sqlalchemy:
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument()
            logger.info("Installed SQLAlchemy auto-instrumentation")
            installed_count += 1
        except ImportError:
            logger.debug("SQLAlchemy not installed, skipping SQLAlchemy instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install SQLAlchemy instrumentation: {e}")
    
    # HTTP client instrumentation (requests, httpx, urllib)
    if enable_requests:
        # requests library
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            RequestsInstrumentor().instrument()
            logger.info("Installed requests library auto-instrumentation")
            installed_count += 1
        except ImportError:
            logger.debug("requests not installed, skipping requests instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install requests instrumentation: {e}")
        
        # httpx library  
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
            logger.info("Installed httpx auto-instrumentation")
            installed_count += 1
        except ImportError:
            logger.debug("httpx not installed, skipping httpx instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install httpx instrumentation: {e}")
        
        # urllib (stdlib)
        try:
            from opentelemetry.instrumentation.urllib import URLLibInstrumentor
            URLLibInstrumentor().instrument()
            logger.info("Installed urllib auto-instrumentation")
            installed_count += 1
        except ImportError:
            pass  # Always available in stdlib
        except Exception as e:
            logger.warning(f"Failed to install urllib instrumentation: {e}")
    
    # Redis instrumentation
    if enable_redis:
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            RedisInstrumentor().instrument()
            logger.info("Installed Redis auto-instrumentation")
            installed_count += 1
        except ImportError:
            logger.debug("Redis not installed, skipping Redis instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install Redis instrumentation: {e}")
    
    # Celery instrumentation
    if enable_celery:
        try:
            from opentelemetry.instrumentation.celery import CeleryInstrumentor
            CeleryInstrumentor().instrument()
            logger.info("Installed Celery auto-instrumentation")
            installed_count += 1
        except ImportError:
            logger.debug("Celery not installed, skipping Celery instrumentation")
        except Exception as e:
            logger.warning(f"Failed to install Celery instrumentation: {e}")
    
    if installed_count > 0:
        logger.info(f"Successfully installed {installed_count} auto-instrumentations")
        _instrumentation_installed = True
        return True
    else:
        logger.warning("No auto-instrumentation could be installed")
        return False
