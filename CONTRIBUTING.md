# Contributing to RootSense Python SDK

Thank you for your interest in contributing to RootSense Python SDK! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/rootsense-python-sdk.git
   cd rootsense-python-sdk
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/paschmaria/rootsense-python-sdk.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv

### Setup Development Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks** (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Project Structure

```
rootsense-python-sdk/
├── rootsense/              # Main package directory
│   ├── __init__.py        # Package initialization and public API
│   ├── client.py          # Core RootSense client
│   ├── config.py          # Configuration management
│   ├── context.py         # Context management (breadcrumbs, tags, user)
│   ├── collectors/        # Data collectors
│   │   ├── error_collector.py      # Exception and error collection
│   │   └── prometheus_collector.py # Metrics collection
│   ├── integrations/      # Framework integrations
│   │   ├── flask.py       # Flask middleware
│   │   ├── fastapi.py     # FastAPI middleware
│   │   └── django.py      # Django middleware
│   ├── transport/         # Data transport layer
│   │   ├── http_transport.py      # HTTP-based transport
│   │   └── websocket_transport.py # WebSocket transport
│   └── utils/             # Utility modules
│       ├── fingerprint.py # Error fingerprinting
│       └── sanitizer.py   # PII sanitization
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
├── examples/             # Example applications
├── docs/                 # Documentation
├── pyproject.toml        # Project metadata and dependencies
└── setup.py              # Setup configuration
```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### Making Changes

1. **Write your code** following the project's style guidelines
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run tests** to ensure everything works
5. **Commit your changes** with clear messages

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(collectors): add support for custom error grouping

fix(transport): handle connection timeout gracefully

docs(readme): add FastAPI integration example

test(client): add unit tests for error capturing
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rootsense --cov-report=html

# Run specific test file
pytest tests/unit/test_client.py

# Run specific test
pytest tests/unit/test_client.py::TestClient::test_capture_exception

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

### Writing Tests

Tests are located in the `tests/` directory and mirror the structure of the main package.

Example test:
```python
import pytest
from rootsense import RootSenseClient
from rootsense.config import Config


class TestClient:
    def test_capture_exception(self):
        """Test basic exception capture."""
        config = Config(
            api_key="test-key",
            project_id="test-project"
        )
        client = RootSenseClient(config)
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = client.capture_exception(e)
            
        assert event_id is not None
        client.close()
```

### Test Coverage

We aim for >80% test coverage. Check coverage with:

```bash
pytest --cov=rootsense --cov-report=term-missing
```

## Code Style

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`

### Formatting

We use `black` for code formatting:

```bash
# Format all files
black rootsense/ tests/

# Check formatting without making changes
black --check rootsense/ tests/
```

### Linting

```bash
# Run flake8
flake8 rootsense/ tests/

# Run mypy for type checking
mypy rootsense/
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Optional, Dict, Any

def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Optional[str]:
    """Capture an exception."""
    pass
```

## Submitting Changes

### Before Submitting

1. **Ensure all tests pass**: `pytest`
2. **Check code style**: `black --check rootsense/ tests/`
3. **Run linters**: `flake8 rootsense/ tests/`
4. **Update documentation** if needed
5. **Add/update tests** for your changes

### Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a pull request** on GitHub with:
   - Clear title and description
   - Reference any related issues
   - List of changes made
   - Screenshots (if UI changes)
   - Test results

3. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] All tests pass
   - [ ] Added new tests
   - [ ] Updated existing tests
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   ```

### Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR

## Release Process

Releases are handled by maintainers. The process involves:

1. **Version bump** in `pyproject.toml` and `rootsense/__init__.py`
2. **Update CHANGELOG.md** with release notes
3. **Create a git tag**: `git tag v0.2.0`
4. **Build distribution**: `python -m build`
5. **Upload to PyPI**: `twine upload dist/*`

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Development Tips

### Local Testing with Real Backend

To test against a local backend:

```python
import rootsense

rootsense.init(
    api_key="test-key",
    project_id="test-project",
    api_url="http://localhost:8000"  # Your local backend
)
```

### Debugging

Enable debug mode to see detailed logs:

```python
import logging
import rootsense

logging.basicConfig(level=logging.DEBUG)

rootsense.init(
    api_key="test-key",
    project_id="test-project",
    debug=True
)
```

### Common Issues

#### Import Errors
```bash
# Reinstall in development mode
pip install -e ".[dev]"
```

#### Test Failures
```bash
# Clear pytest cache
pytest --cache-clear
```

#### Type Checking Issues
```bash
# Install type stubs
pip install types-requests types-python-dateutil
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Capture an exception and send it to RootSense.
    
    Args:
        exception: The exception to capture.
        context: Additional context information.
        
    Returns:
        Event ID if captured successfully, None otherwise.
        
    Raises:
        ValueError: If exception is not an Exception instance.
        
    Example:
        >>> try:
        ...     raise ValueError("Test")
        ... except Exception as e:
        ...     event_id = capture_exception(e)
    """
    pass
```

## Questions?

- **Documentation**: [docs.rootsense.ai](https://docs.rootsense.ai)
- **Discussions**: [GitHub Discussions](https://github.com/paschmaria/rootsense-python-sdk/discussions)
- **Issues**: [GitHub Issues](https://github.com/paschmaria/rootsense-python-sdk/issues)
- **Email**: support@rootsense.ai

Thank you for contributing! 🎉
