"""Tests for GET /api/v3/health endpoint."""

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, app_client):
        response = app_client.get('/api/v3/health')
        assert response.status_code == 200

    def test_health_returns_ok_status(self, app_client):
        response = app_client.get('/api/v3/health')
        data = response.json()
        assert data['status'] == 'OK'
        assert data['message'] == ''

    def test_health_does_not_require_auth(self, app_client):
        response = app_client.get('/api/v3/health')
        assert response.status_code == 200
