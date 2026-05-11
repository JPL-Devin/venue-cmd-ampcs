"""Tests for request validation and error handling."""

import json
import pytest
from unittest.mock import patch


class TestRequestValidation:
    def test_missing_required_field_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'sessionId': 1},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_wrong_type_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'sessionId': 'not_an_int', 'commandString': 'CMD_NO_OP'},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_both_session_id_and_data_path_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'sessionId': 1, 'dataPath': 'dp-alpha', 'commandString': 'CMD_NO_OP'},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_neither_session_id_nor_data_path_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'commandString': 'CMD_NO_OP'},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_invalid_enum_value_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/mtak/start',
            json={'sessions': [{'sessionId': 1}], 'defaultCmdString': 'INVALID'},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_timeout_below_minimum_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/mtak/start',
            json={'sessions': [{'sessionId': 1}], 'timeout': 10},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_negative_timeout_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={'sessionId': 1, 'commandString': 'CMD_NO_OP', 'timeout': -1},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_empty_json_body_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_invalid_json_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/fsw_cmd',
            content=b'not json',
            headers={**auth_headers, 'Content-Type': 'application/json'}
        )
        assert response.status_code == 400

    def test_missing_sessions_for_mtak_start_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/mtak/start',
            json={'timeout': 30},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_binary_file_missing_required_fields_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/cmd/binary_file',
            json={'sessionId': 1, 'sourceFilePath': '/path'},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_evr_missing_session_id_returns_400(self, app_client, auth_headers):
        response = app_client.request(
            'GET',
            '/api/v3/evr/realtime',
            json={
                'startTime': '2024-100T12:00:00',
                'endTime': '2024-100T13:00:00'
            },
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_eha_missing_channel_ids_returns_400(self, app_client, auth_headers):
        response = app_client.request(
            'GET',
            '/api/v3/eha/realtime',
            json={
                'startTime': '2024-100T12:00:00',
                'endTime': '2024-100T13:00:00'
            },
            headers=auth_headers
        )
        assert response.status_code == 400
