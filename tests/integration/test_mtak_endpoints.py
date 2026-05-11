"""Tests for MTAK start/shutdown endpoints."""

import pytest
from unittest.mock import patch


class TestMtakStart:
    def test_start_mtak_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_start_mtak') as mock_start:
            mock_start.return_value = ([1], '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/mtak/start',
                json={'sessionIds': [1], 'timeout': 30, 'defaultCmdString': 'AB'},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data['sessionIds'] == [1]
            assert data['startTime'] == '2024-04-10T12:00:00.000Z'

    def test_start_mtak_multiple_sessions(self, app_client, auth_headers):
        with patch('core.venue_core.core_start_mtak') as mock_start:
            mock_start.return_value = ([1, 2], '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/mtak/start',
                json={'sessionIds': [1, 2], 'timeout': 60},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data['sessionIds'] == [1, 2]

    def test_start_mtak_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_start_mtak', side_effect=Exception('MTAK failed')):
            response = app_client.post(
                '/api/v3/mtak/start',
                json={'sessionIds': [1], 'timeout': 30},
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Unexpected error' in response.json()['message']

    def test_start_mtak_requires_auth(self, app_client):
        response = app_client.post(
            '/api/v3/mtak/start',
            json={'sessionIds': [1], 'timeout': 30}
        )
        assert response.status_code == 401

    def test_start_mtak_default_cmd_string_A(self, app_client, auth_headers):
        with patch('core.venue_core.core_start_mtak') as mock_start:
            mock_start.return_value = ([1], '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/mtak/start',
                json={'sessionIds': [1], 'timeout': 30, 'defaultCmdString': 'A'},
                headers=auth_headers
            )
            assert response.status_code == 200
            mock_start.assert_called_once_with(sessionIds=[1], defaultCmdString='A', timeout=30)


class TestMtakShutdown:
    def test_shutdown_mtak_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_stop_mtak', return_value=''):
            response = app_client.post('/api/v3/mtak/shutdown', headers=auth_headers)
            assert response.status_code == 204

    def test_shutdown_mtak_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_stop_mtak', side_effect=Exception('shutdown failed')):
            response = app_client.post('/api/v3/mtak/shutdown', headers=auth_headers)
            assert response.status_code == 400
            assert 'Unexpected error' in response.json()['message']

    def test_shutdown_mtak_requires_auth(self, app_client):
        response = app_client.post('/api/v3/mtak/shutdown')
        assert response.status_code == 401
