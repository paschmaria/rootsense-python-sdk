"""Automatic instrumentation setup using OpenTelemetry."""

import logging
from typing import Optional

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class AutoInstrumentation:
    """Manages automatic instrumentation via OpenTelemetry."""

    def __init__(self, error_collector, http_transport, config):
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning(
                "OpenTelemetry not installed. Install with: pip install rootsense[instrumentation]"
            )
            return
        
        self.error_collector = error_collector
        self.http_transport = http_transport
        self.config = config
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize OpenTelemetry with custom exporters."""
        if not OPENTELEMETRY_AVAILABLE:
            return False
        
        if self._initialized:
            logger.debug("Auto-instrumentation already initialized")
            return True
        
        try:
            # Import exporters
            from rootsense.instrumentation.exporters import (
                RootSenseSpanExporter,
                RootSenseMetricExporter
            )
            
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.config.service_name or "unknown",
                "service.version": self.config.service_version or "unknown",
                "deployment.environment": self.config.environment or "production",
                "rootsense.project_id": self.config.project_id
            })
            
            # Setup tracing
            span_exporter = RootSenseSpanExporter(self.error_collector, self.http_transport)
            tracer_provider = TracerProvider(resource=resource)
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
            trace.set_tracer_provider(tracer_provider)
            
            # Setup metrics
            metric_exporter = RootSenseMetricExporter(self.http_transport)
            metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(meter_provider)
            
            # Enable auto-instrumentation for installed frameworks
            self._enable_auto_instrumentation()
            
            self._initialized = True
            logger.info("OpenTelemetry auto-instrumentation initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize auto-instrumentation: {e}")
            return False

    def _enable_auto_instrumentation(self):
        """Enable automatic instrumentation for available frameworks."""
        instrumentors = []
        
        # Django
        try:
            from opentelemetry.instrumentation.django import DjangoInstrumentor
            DjangoInstrumentor().instrument()
            instrumentors.append('Django')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument Django: {e}")
        
        # Flask
        try:
            from opentelemetry.instrumentation.flask import FlaskInstrumentor
            FlaskInstrumentor().instrument()
            instrumentors.append('Flask')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument Flask: {e}")
        
        # SQLAlchemy
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument()
            instrumentors.append('SQLAlchemy')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument SQLAlchemy: {e}")
        
        # Requests
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            RequestsInstrumentor().instrument()
            instrumentors.append('Requests')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument Requests: {e}")
        
        # HTTPX
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
            instrumentors.append('HTTPX')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument HTTPX: {e}")
        
        # Redis
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            RedisInstrumentor().instrument()
            instrumentors.append('Redis')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument Redis: {e}")
        
        # Celery
        try:
            from opentelemetry.instrumentation.celery import CeleryInstrumentor
            CeleryInstrumentor().instrument()
            instrumentors.append('Celery')
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not instrument Celery: {e}")
        
        if instrumentors:
            logger.info(f"Auto-instrumentation enabled for: {', '.join(instrumentors)}")
        else:
            logger.info("No frameworks detected for auto-instrumentation")

    def shutdown(self):
        """Shutdown auto-instrumentation."""
        if not OPENTELEMETRY_AVAILABLE or not self._initialized:
            return
        
        try:
            # Shutdown tracer provider
            tracer_provider = trace.get_tracer_provider()
            if hasattr(tracer_provider, 'shutdown'):
                tracer_provider.shutdown()
            
            # Shutdown meter provider
            meter_provider = metrics.get_meter_provider()
            if hasattr(meter_provider, 'shutdown'):
                meter_provider.shutdown()
            
            logger.info("Auto-instrumentation shutdown complete")
        except Exception as e:
            logger.error(f"Error during auto-instrumentation shutdown: {e}")
