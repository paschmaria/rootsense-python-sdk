"""Tests for framework integrations."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestFlaskIntegration:
    """Test Flask integration."""

    @pytest.fixture
    def flask_app(self):
        """Create a test Flask app."""
        try:
            from flask import Flask
            app = Flask(__name__)
            
            @app.route('/test')
            def test_route():
                return 'OK'
            
            @app.route('/error')
            def error_route():
                raise ValueError("Test error")
            
            return app
        except ImportError:
            pytest.skip("Flask not installed")

    def test_flask_integration_initialization(self, flask_app, mock_client):
        """Test Flask integration initializes correctly."""
        from rootsense.integrations.flask import FlaskIntegration
        
        with patch('rootsense.integrations.flask.get_client', return_value=mock_client):
            integration = FlaskIntegration(flask_app)
            
            assert integration.client == mock_client

    def test_flask_error_capture(self, flask_app, mock_client):
        """Test Flask integration captures errors."""
        from rootsense.integrations.flask import FlaskIntegration
        
        with patch('rootsense.integrations.flask.get_client', return_value=mock_client):
            integration = FlaskIntegration(flask_app)
            
            with flask_app.test_client() as client:
                response = client.get('/error')
                
                # Should have captured the exception
                assert mock_client.capture_exception.called

    def test_flask_successful_request(self, flask_app, mock_client):
        """Test Flask integration handles successful requests."""
        from rootsense.integrations.flask import FlaskIntegration
        
        with patch('rootsense.integrations.flask.get_client', return_value=mock_client):
            integration = FlaskIntegration(flask_app)
            
            with flask_app.test_client() as client:
                response = client.get('/test')
                
                assert response.status_code == 200
                # Should not capture exception for successful request
                assert not mock_client.capture_exception.called


class TestFastAPIIntegration:
    """Test FastAPI integration."""

    @pytest.fixture
    def fastapi_app(self):
        """Create a test FastAPI app."""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            
            app = FastAPI()
            
            @app.get('/test')
            async def test_route():
                return {'message': 'OK'}
            
            @app.get('/error')
            async def error_route():
                raise ValueError("Test error")
            
            return app
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_fastapi_integration_initialization(self, fastapi_app, mock_client):
        """Test FastAPI integration initializes correctly."""
        from rootsense.integrations.fastapi import FastAPIIntegration
        
        with patch('rootsense.integrations.fastapi.get_client', return_value=mock_client):
            integration = FastAPIIntegration(fastapi_app)
            
            assert integration.client == mock_client

    @pytest.mark.asyncio
    async def test_fastapi_error_capture(self, fastapi_app, mock_client):
        """Test FastAPI integration captures errors."""
        from rootsense.integrations.fastapi import FastAPIIntegration
        from fastapi.testclient import TestClient
        
        with patch('rootsense.integrations.fastapi.get_client', return_value=mock_client):
            integration = FastAPIIntegration(fastapi_app)
            
            client = TestClient(fastapi_app)
            
            try:
                response = client.get('/error')
            except:
                pass
            
            # Should have captured the exception
            assert mock_client.capture_exception.called

    @pytest.mark.asyncio
    async def test_fastapi_successful_request(self, fastapi_app, mock_client):
        """Test FastAPI integration handles successful requests."""
        from rootsense.integrations.fastapi import FastAPIIntegration
        from fastapi.testclient import TestClient
        
        with patch('rootsense.integrations.fastapi.get_client', return_value=mock_client):
            integration = FastAPIIntegration(fastapi_app)
            
            client = TestClient(fastapi_app)
            response = client.get('/test')
            
            assert response.status_code == 200


class TestDjangoMiddleware:
    """Test Django middleware."""

    def test_django_middleware_initialization(self, mock_client):
        """Test Django middleware initializes correctly."""
        try:
            from rootsense.integrations.django import DjangoMiddleware
            
            get_response = Mock()
            
            with patch('rootsense.integrations.django.get_client', return_value=mock_client):
                middleware = DjangoMiddleware(get_response)
                
                assert middleware.client == mock_client
        except ImportError:
            pytest.skip("Django not installed")

    def test_django_request_processing(self, mock_client):
        """Test Django middleware processes requests."""
        try:
            from rootsense.integrations.django import DjangoMiddleware
            from django.http import HttpRequest, HttpResponse
            
            get_response = Mock(return_value=HttpResponse("OK"))
            
            with patch('rootsense.integrations.django.get_client', return_value=mock_client):
                middleware = DjangoMiddleware(get_response)
                
                request = HttpRequest()
                request.method = 'GET'
                request.path = '/test'
                
                response = middleware(request)
                
                assert response.status_code == 200
                get_response.assert_called_once()
        except ImportError:
            pytest.skip("Django not installed")

    def test_django_exception_handling(self, mock_client):
        """Test Django middleware handles exceptions."""
        try:
            from rootsense.integrations.django import DjangoMiddleware
            from django.http import HttpRequest
            
            def get_response(request):
                raise ValueError("Test error")
            
            with patch('rootsense.integrations.django.get_client', return_value=mock_client):
                middleware = DjangoMiddleware(get_response)
                
                request = HttpRequest()
                request.method = 'GET'
                request.path = '/error'
                
                with pytest.raises(ValueError):
                    middleware(request)
                
                # Should have captured the exception
                assert mock_client.capture_exception.called
        except ImportError:
            pytest.skip("Django not installed")


class TestASGIMiddleware:
    """Test ASGI middleware."""

    @pytest.mark.asyncio
    async def test_asgi_middleware_http_request(self, mock_client):
        """Test ASGI middleware handles HTTP requests."""
        from rootsense.integrations.asgi import ASGIMiddleware
        
        async def app(scope, receive, send):
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            await send({
                'type': 'http.response.body',
                'body': b'OK',
            })
        
        with patch('rootsense.integrations.asgi.get_client', return_value=mock_client):
            middleware = ASGIMiddleware(app)
            
            scope = {
                'type': 'http',
                'method': 'GET',
                'path': '/test',
                'query_string': b'',
                'headers': [],
            }
            
            received = []
            async def receive():
                return {'type': 'http.request', 'body': b''}
            
            async def send(message):
                received.append(message)
            
            await middleware(scope, receive, send)
            
            assert any(msg['type'] == 'http.response.start' for msg in received)

    @pytest.mark.asyncio
    async def test_asgi_middleware_error_capture(self, mock_client):
        """Test ASGI middleware captures errors."""
        from rootsense.integrations.asgi import ASGIMiddleware
        
        async def app(scope, receive, send):
            raise ValueError("Test error")
        
        with patch('rootsense.integrations.asgi.get_client', return_value=mock_client):
            middleware = ASGIMiddleware(app)
            
            scope = {
                'type': 'http',
                'method': 'GET',
                'path': '/error',
                'query_string': b'',
                'headers': [],
            }
            
            async def receive():
                return {'type': 'http.request', 'body': b''}
            
            async def send(message):
                pass
            
            with pytest.raises(ValueError):
                await middleware(scope, receive, send)
            
            assert mock_client.capture_exception.called


class TestWSGIMiddleware:
    """Test WSGI middleware."""

    def test_wsgi_middleware_successful_request(self, mock_client):
        """Test WSGI middleware handles successful requests."""
        from rootsense.integrations.wsgi import WSGIMiddleware
        
        def app(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [b'OK']
        
        with patch('rootsense.integrations.wsgi.get_client', return_value=mock_client):
            middleware = WSGIMiddleware(app)
            
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/test',
                'QUERY_STRING': '',
                'REMOTE_ADDR': '127.0.0.1',
            }
            
            responses = []
            def start_response(status, headers, exc_info=None):
                responses.append(status)
                return lambda data: None
            
            result = middleware(environ, start_response)
            
            assert b'OK' in list(result)
            assert '200 OK' in responses

    def test_wsgi_middleware_error_capture(self, mock_client):
        """Test WSGI middleware captures errors."""
        from rootsense.integrations.wsgi import WSGIMiddleware
        
        def app(environ, start_response):
            raise ValueError("Test error")
        
        with patch('rootsense.integrations.wsgi.get_client', return_value=mock_client):
            middleware = WSGIMiddleware(app)
            
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/error',
                'QUERY_STRING': '',
                'REMOTE_ADDR': '127.0.0.1',
            }
            
            def start_response(status, headers, exc_info=None):
                return lambda data: None
            
            with pytest.raises(ValueError):
                middleware(environ, start_response)
            
            assert mock_client.capture_exception.called
