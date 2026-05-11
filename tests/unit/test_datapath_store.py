"""Tests for the in-memory DataPath store in core/datapath_store.py"""

import pytest

from core import datapath_store


@pytest.fixture(autouse=True)
def _clear_store():
    datapath_store.clear()
    yield
    datapath_store.clear()


class TestSetDatapath:
    def test_set_and_get(self):
        datapath_store.set_datapath('dp-alpha', 42)
        assert datapath_store.get_session_id('dp-alpha') == 42

    def test_set_overwrites(self):
        datapath_store.set_datapath('dp-alpha', 1)
        datapath_store.set_datapath('dp-alpha', 2)
        assert datapath_store.get_session_id('dp-alpha') == 2


class TestGetSessionId:
    def test_missing_key_raises(self):
        with pytest.raises(KeyError):
            datapath_store.get_session_id('missing')


class TestDeleteDatapath:
    def test_delete_existing(self):
        datapath_store.set_datapath('dp-alpha', 1)
        datapath_store.delete_datapath('dp-alpha')
        with pytest.raises(KeyError):
            datapath_store.get_session_id('dp-alpha')

    def test_delete_missing_raises(self):
        with pytest.raises(KeyError):
            datapath_store.delete_datapath('missing')


class TestListDatapaths:
    def test_empty(self):
        assert datapath_store.list_datapaths() == {}

    def test_populated(self):
        datapath_store.set_datapath('dp-a', 1)
        datapath_store.set_datapath('dp-b', 2)
        snapshot = datapath_store.list_datapaths()
        assert snapshot == {'dp-a': 1, 'dp-b': 2}

    def test_returned_dict_is_a_copy(self):
        datapath_store.set_datapath('dp-a', 1)
        snapshot = datapath_store.list_datapaths()
        snapshot['dp-a'] = 999
        assert datapath_store.get_session_id('dp-a') == 1
