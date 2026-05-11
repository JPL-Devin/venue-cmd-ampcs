"""Tests for GET /api/v3/evr/realtime endpoint.

Note: These endpoints use GET with a JSON body. Starlette's TestClient.get()
doesn't support json=, so we use client.request('GET', ..., json=...).
"""

import json
import pytest
from unittest.mock import patch


class TestEvrRealtime:
    def test_evr_realtime_success(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_evr_multi') as mock_evr:
            mock_evr.return_value = [
                {
                    'evrName': 'TEST_EVR', 'sessionId': 1, 'eventId': 100,
                    'vcId': 0, 'evrLevel': 'ACTIVITY', 'fromSSE': False,
                    'evrMessage': 'test message', 'evrModule': None,
                    'sclk': '0001234-56789', 'ert': '2024-04-10T12:00:00.000Z',
                    'scet': '2024-04-10T11:59:50.000Z', 'isRecorded': False
                }
            ]
            response = app_client.request(
                'GET',
                '/api/v3/evr/realtime',
                json={
                    'sessionId': 1,
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]['evrName'] == 'TEST_EVR'

    def test_evr_realtime_with_filters(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_evr_multi') as mock_evr:
            mock_evr.return_value = []
            response = app_client.request(
                'GET',
                '/api/v3/evr/realtime',
                json={
                    'sessionId': 1,
                    'evrNames': ['EVR_A', 'EVR_B'],
                    'eventIds': [100, 200],
                    'evrLevels': ['ACTIVITY'],
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00',
                    'timeout': 120
                },
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_evr_realtime_empty_results(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_evr_multi') as mock_evr:
            mock_evr.return_value = []
            response = app_client.request(
                'GET',
                '/api/v3/evr/realtime',
                json={
                    'sessionId': 1,
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json() == []

    def test_evr_realtime_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_evr_multi', side_effect=Exception('query failed')):
            response = app_client.request(
                'GET',
                '/api/v3/evr/realtime',
                json={
                    'sessionId': 1,
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to query realtime EVR' in response.json()['message']

    def test_evr_realtime_requires_auth(self, app_client):
        response = app_client.request(
            'GET',
            '/api/v3/evr/realtime',
            content=json.dumps({
                'sessionId': 1,
                'startTime': '2024-100T12:00:00',
                'endTime': '2024-100T13:00:00'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 401
