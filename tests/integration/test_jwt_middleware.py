"""Tests for JWT authentication middleware."""

import pytest


class TestJwtMiddleware:
    def test_missing_auth_header_returns_401(self, app_client):
        response = app_client.post('/api/v3/mtak/shutdown')
        assert response.status_code == 401
        assert 'Invalid API token' in response.json()['message']

    def test_malformed_auth_header_returns_401(self, app_client):
        response = app_client.post(
            '/api/v3/mtak/shutdown',
            headers={'Authorization': 'Basic sometoken'}
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(self, app_client, expired_auth_headers):
        response = app_client.post(
            '/api/v3/mtak/shutdown',
            headers=expired_auth_headers
        )
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, app_client):
        response = app_client.post(
            '/api/v3/mtak/shutdown',
            headers={'Authorization': 'Bearer invalidtoken123'}
        )
        assert response.status_code == 401

    def test_valid_token_passes_through(self, app_client, auth_headers):
        from unittest.mock import patch
        with patch('core.venue_core.core_stop_mtak', return_value=''):
            response = app_client.post('/api/v3/mtak/shutdown', headers=auth_headers)
            # Should not be 401 - either 204 (success) or other status
            assert response.status_code != 401

    def test_health_bypasses_jwt(self, app_client):
        response = app_client.get('/api/v3/health')
        assert response.status_code == 200

    def test_docs_bypass_jwt(self, app_client):
        response = app_client.get('/docs')
        assert response.status_code == 200

    def test_openapi_json_bypasses_jwt(self, app_client):
        response = app_client.get('/openapi.json')
        assert response.status_code == 200
