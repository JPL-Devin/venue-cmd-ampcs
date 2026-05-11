"""Tests for the /api/v3/datapath CRUD endpoints."""

import pytest

from core import datapath_store


@pytest.fixture(autouse=True)
def _clear_store():
    datapath_store.clear()
    yield
    datapath_store.clear()


class TestCreateDatapath:
    def test_create_success(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/datapath',
            json={'dataPath': 'dp-alpha', 'sessionId': 42},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['dataPath'] == 'dp-alpha'
        assert data['sessionId'] == 42
        assert datapath_store.get_session_id('dp-alpha') == 42

    def test_create_overwrites_existing(self, app_client, auth_headers):
        datapath_store.set_datapath('dp-alpha', 1)
        response = app_client.post(
            '/api/v3/datapath',
            json={'dataPath': 'dp-alpha', 'sessionId': 2},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert datapath_store.get_session_id('dp-alpha') == 2

    def test_create_missing_session_id_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/datapath',
            json={'dataPath': 'dp-alpha'},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_missing_data_path_returns_400(self, app_client, auth_headers):
        response = app_client.post(
            '/api/v3/datapath',
            json={'sessionId': 42},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_requires_auth(self, app_client):
        response = app_client.post(
            '/api/v3/datapath',
            json={'dataPath': 'dp-alpha', 'sessionId': 42}
        )
        assert response.status_code == 401


class TestGetDatapath:
    def test_get_success(self, app_client, auth_headers):
        datapath_store.set_datapath('dp-alpha', 42)
        response = app_client.get(
            '/api/v3/datapath/dp-alpha',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['dataPath'] == 'dp-alpha'
        assert data['sessionId'] == 42

    def test_get_missing_returns_404(self, app_client, auth_headers):
        response = app_client.get(
            '/api/v3/datapath/missing',
            headers=auth_headers
        )
        assert response.status_code == 404
        assert 'DataPath not found' in response.json()['message']

    def test_get_requires_auth(self, app_client):
        response = app_client.get('/api/v3/datapath/dp-alpha')
        assert response.status_code == 401

    def test_get_data_path_named_health_still_requires_auth(self, app_client):
        # Regression: the health-endpoint JWT bypass must match the exact
        # /api/v3/health path, not arbitrary paths ending in /health.
        response = app_client.get('/api/v3/datapath/health')
        assert response.status_code == 401


class TestDeleteDatapath:
    def test_delete_success(self, app_client, auth_headers):
        datapath_store.set_datapath('dp-alpha', 42)
        response = app_client.delete(
            '/api/v3/datapath/dp-alpha',
            headers=auth_headers
        )
        assert response.status_code == 204
        with pytest.raises(KeyError):
            datapath_store.get_session_id('dp-alpha')

    def test_delete_missing_returns_404(self, app_client, auth_headers):
        response = app_client.delete(
            '/api/v3/datapath/missing',
            headers=auth_headers
        )
        assert response.status_code == 404
        assert 'DataPath not found' in response.json()['message']

    def test_delete_requires_auth(self, app_client):
        response = app_client.delete('/api/v3/datapath/dp-alpha')
        assert response.status_code == 401

    def test_delete_data_path_named_health_still_requires_auth(self, app_client):
        # Regression: the health-endpoint JWT bypass must match the exact
        # /api/v3/health path, not arbitrary paths ending in /health.
        response = app_client.delete('/api/v3/datapath/health')
        assert response.status_code == 401


class TestDatapathRoundTrip:
    def test_create_get_delete_get(self, app_client, auth_headers):
        # create
        response = app_client.post(
            '/api/v3/datapath',
            json={'dataPath': 'dp-roundtrip', 'sessionId': 7},
            headers=auth_headers
        )
        assert response.status_code == 200

        # get
        response = app_client.get(
            '/api/v3/datapath/dp-roundtrip',
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == {'dataPath': 'dp-roundtrip', 'sessionId': 7}

        # delete
        response = app_client.delete(
            '/api/v3/datapath/dp-roundtrip',
            headers=auth_headers
        )
        assert response.status_code == 204

        # get -> 404
        response = app_client.get(
            '/api/v3/datapath/dp-roundtrip',
            headers=auth_headers
        )
        assert response.status_code == 404
