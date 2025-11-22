# Changelog

All notable changes to the RootSense Python SDK.

## [0.1.0] - 2024-11-22

### Added
- Initial release of RootSense Python SDK
- Core error tracking and event capture
- Automatic context enrichment
- Built-in Prometheus metrics
- HTTP transport with batching and retry
- PII sanitization
- Flask, FastAPI, Django integrations
- Performance monitoring
- Distributed tracing
- Connection string configuration
- Comprehensive tests and examples

### Changed
- Simplified to HTTP-only transport
- Integrated metrics into ErrorCollector
- Unified configuration API

### Removed
- Separate PrometheusCollector (merged)
- WebSocket transport (simplified)
