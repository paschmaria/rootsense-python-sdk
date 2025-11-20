"""Distributed tracing for RootSense."""

from rootsense.tracing.tracer import Tracer, get_tracer, trace_function

__all__ = [
    "Tracer",
    "get_tracer",
    "trace_function",
]
