"""Tests for command dispatch endpoints."""

import pytest
from unittest.mock import patch


class TestFswCmd:
    def test_fsw_cmd_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_fsw_cmd') as mock_send:
            mock_send.return_value = ('CMD_NO_OP', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/fsw_cmd',
                json={'sessionId': 1, 'commandString': 'CMD_NO_OP'},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data['cmdRequested'] == 'CMD_NO_OP'
            assert 'dispatchTime' in data

    def test_fsw_cmd_with_string_selection(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_fsw_cmd') as mock_send:
            mock_send.return_value = ('CMD_NO_OP', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/fsw_cmd',
                json={'sessionId': 1, 'commandString': 'CMD_NO_OP', 'stringSelection': 'A'},
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_fsw_cmd_validate_false(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_fsw_cmd') as mock_send:
            mock_send.return_value = ('CMD_NO_OP', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/fsw_cmd',
                json={'sessionId': 1, 'commandString': 'CMD_NO_OP', 'validate': False},
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_fsw_cmd_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_fsw_cmd', side_effect=Exception('cmd failed')):
            response = app_client.post(
                '/api/v3/cmd/fsw_cmd',
                json={'sessionId': 1, 'commandString': 'CMD_BAD'},
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to send FSW command' in response.json()['message']

    def test_fsw_cmd_requires_auth(self, app_client):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'sessionId': 1, 'commandString': 'CMD_NO_OP'}
        )
        assert response.status_code == 401

    def test_fsw_cmd_with_data_path(self, app_client, auth_headers):
        from core import datapath_store
        datapath_store.clear()
        datapath_store.set_datapath('dp-alpha', 17)
        try:
            with patch('core.venue_core.core_send_fsw_cmd') as mock_send:
                mock_send.return_value = ('CMD_NO_OP', '2024-04-10T12:00:00.000Z')
                response = app_client.post(
                    '/api/v3/cmd/fsw_cmd',
                    json={'dataPath': 'dp-alpha', 'commandString': 'CMD_NO_OP'},
                    headers=auth_headers
                )
                assert response.status_code == 200
                kwargs = mock_send.call_args.kwargs
                assert kwargs['sessionId'] == 17
        finally:
            datapath_store.clear()

    def test_fsw_cmd_with_unknown_data_path_returns_400(self, app_client, auth_headers):
        from core import datapath_store
        datapath_store.clear()
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'dataPath': 'missing-dp', 'commandString': 'CMD_NO_OP'},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert 'DataPath not found' in response.json()['message']


class TestHwCmd:
    def test_hw_cmd_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_hw_cmd') as mock_send:
            mock_send.return_value = ('HW_CMD_STEM', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/hw_cmd',
                json={'sessionId': 1, 'commandStem': 'HW_CMD_STEM'},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data['cmdRequested'] == 'HW_CMD_STEM'

    def test_hw_cmd_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_hw_cmd', side_effect=Exception('hw cmd failed')):
            response = app_client.post(
                '/api/v3/cmd/hw_cmd',
                json={'sessionId': 1, 'commandStem': 'HW_CMD_BAD'},
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to send HW command' in response.json()['message']

    def test_hw_cmd_requires_auth(self, app_client):
        response = app_client.post(
            '/api/v3/cmd/hw_cmd',
            json={'sessionId': 1, 'commandStem': 'HW_CMD_STEM'}
        )
        assert response.status_code == 401


class TestSseCmd:
    def test_sse_cmd_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_sse_cmd') as mock_send:
            mock_send.return_value = ('SSE_CMD', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/sse',
                json={'sessionId': 1, 'commandString': 'SSE_CMD'},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data['cmdRequested'] == 'SSE_CMD'

    def test_sse_cmd_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_sse_cmd', side_effect=Exception('sse failed')):
            response = app_client.post(
                '/api/v3/cmd/sse',
                json={'sessionId': 1, 'commandString': 'SSE_CMD'},
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to send SSE command' in response.json()['message']


class TestBinaryFile:
    def test_binary_file_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_fsw_file') as mock_send:
            mock_send.return_value = ('file info', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/binary_file',
                json={
                    'sessionId': 1,
                    'sourceFilePath': '/path/to/file.bin',
                    'targetFilePath': '/eng1/file.bin',
                    'fileType': 1
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert 'cmdRequested' in data
            assert 'dispatchTime' in data

    def test_binary_file_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_fsw_file', side_effect=Exception('file failed')):
            response = app_client.post(
                '/api/v3/cmd/binary_file',
                json={
                    'sessionId': 1,
                    'sourceFilePath': '/path/to/file.bin',
                    'targetFilePath': '/eng1/file.bin',
                    'fileType': 1
                },
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to send a file' in response.json()['message']


class TestScmfFile:
    def test_scmf_success(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_scmf_file') as mock_send:
            mock_send.return_value = ('SCMF info', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/scmf',
                json={'sessionId': 1, 'filePath': '/path/to/file.scmf'},
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_scmf_with_disable_checks(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_scmf_file') as mock_send:
            mock_send.return_value = ('SCMF info', '2024-04-10T12:00:00.000Z')
            response = app_client.post(
                '/api/v3/cmd/scmf',
                json={'sessionId': 1, 'filePath': '/path/to/file.scmf', 'disableChecks': True},
                headers=auth_headers
            )
            assert response.status_code == 200

    def test_scmf_exception_returns_400(self, app_client, auth_headers):
        with patch('core.venue_core.core_send_scmf_file', side_effect=Exception('scmf failed')):
            response = app_client.post(
                '/api/v3/cmd/scmf',
                json={'sessionId': 1, 'filePath': '/path/to/file.scmf'},
                headers=auth_headers
            )
            assert response.status_code == 400
            assert 'Failed to send a SCMF file' in response.json()['message']
