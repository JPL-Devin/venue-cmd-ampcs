"""Tests for GET /api/v3/eha/realtime endpoint.

Note: These endpoints use GET with a JSON body. Starlette's TestClient.get()
doesn't support json=, so we use client.request('GET', ..., json=...).
"""

import json
import pytest
from unittest.mock import patch


class TestEhaRealtime:
    def test_eha_realtime_success(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_eha_multi') as mock_eha:
            mock_eha.return_value = [
                {
                    'sessionId': 1, 'channelId': 'CH-0001', 'dn': '42',
                    'eu': 42.0, 'vcId': 0, 'channelName': None,
                    'channelType': 'DN', 'channelStatus': '',
                    'dnAlarmState': 'NONE', 'euAlarmState': 'NONE',
                    'sclk': '0001234-56789', 'ert': '2024-04-10T12:00:00.000Z',
                    'scet': '2024-04-10T11:59:50.000Z', 'isRecorded': False
                }
            ]
            response = app_client.request(
                'GET',
                '/api/v3/eha/realtime',
                json={
                    'sessionId': 1,
                    'channelIds': ['CH-0001'],
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]['channelId'] == 'CH-0001'

    def test_eha_realtime_with_session_id(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_eha_multi') as mock_eha:
            mock_eha.return_value = []
            response = app_client.request(
                'GET',
                '/api/v3/eha/realtime',
                json={
                    'sessionId': 1,
                    'channelIds': ['CH-0001'],
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_eha_realtime_empty_results(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_eha_multi') as mock_eha:
            mock_eha.return_value = []
            response = app_client.request(
                'GET',
                '/api/v3/eha/realtime',
                json={
                    'sessionId': 1,
                    'channelIds': ['CH-0001'],
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json() == []

    def test_eha_realtime_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.get_rt_eha_multi', side_effect=Exception('query failed')):
            response = app_client.request(
                'GET',
                '/api/v3/eha/realtime',
                json={
                    'sessionId': 1,
                    'channelIds': ['CH-0001'],
                    'startTime': '2024-100T12:00:00',
                    'endTime': '2024-100T13:00:00'
                },
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to query realtime EHA' in response.json()['message']

    def test_eha_realtime_requires_auth(self, app_client):
        response = app_client.request(
            'GET',
            '/api/v3/eha/realtime',
            content=json.dumps({
                'sessionId': 1,
                'channelIds': ['CH-0001'],
                'startTime': '2024-100T12:00:00',
                'endTime': '2024-100T13:00:00'
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 401

    def test_eha_realtime_with_data_path(self, app_client, auth_headers):
        from core import datapath_store
        datapath_store.clear()
        datapath_store.set_datapath('dp-beta', 99)
        try:
            with patch('core.venue_core.get_rt_eha_multi') as mock_eha:
                mock_eha.return_value = []
                response = app_client.request(
                    'GET',
                    '/api/v3/eha/realtime',
                    json={
                        'dataPath': 'dp-beta',
                        'channelIds': ['CH-0001'],
                        'startTime': '2024-100T12:00:00',
                        'endTime': '2024-100T13:00:00'
                    },
                    headers=auth_headers
                )
                assert response.status_code == 200
                kwargs = mock_eha.call_args.kwargs
                assert kwargs['sessionId'] == 99
        finally:
            datapath_store.clear()

    def test_eha_realtime_both_session_and_datapath_returns_400(self, app_client, auth_headers):
        response = app_client.request(
            'GET',
            '/api/v3/eha/realtime',
            json={
                'sessionId': 1,
                'dataPath': 'dp-beta',
                'channelIds': ['CH-0001'],
                'startTime': '2024-100T12:00:00',
                'endTime': '2024-100T13:00:00'
            },
            headers=auth_headers
        )
        assert response.status_code == 400
