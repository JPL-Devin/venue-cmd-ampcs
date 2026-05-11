"""Tests for LAD query construction in core/lad_query.py with mocked lad client."""

import pytest
from unittest.mock import patch, MagicMock, call

from core.schema import TimeType
from core import lad_query


class TestLadGetEvrMulti:
    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_builds_correct_query_with_all_filters(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_lad_client = MagicMock()
        mock_client.LadClient.return_value = mock_lad_client
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr_multi(
            sessionId=1, evrNames=['EVR_A', 'EVR_B'],
            eventIds=[100, 200], evrLevels=['ACTIVITY'],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00',
            timeout=120
        )

        mock_evrq.addSessionNumber.assert_called_once_with(1)
        assert mock_evrq.addEvrName.call_count == 2
        mock_evrq.addEvrName.assert_any_call('EVR_A')
        mock_evrq.addEvrName.assert_any_call('EVR_B')
        assert mock_evrq.addEventId.call_count == 2
        mock_evrq.addEvrLevel.assert_called_once_with('ACTIVITY')
        mock_evrq.useErt.assert_called_once()
        mock_evrq.before.assert_called_once_with('2024-100T13:00:00')
        mock_evrq.after.assert_called_once_with('2024-100T12:00:00')
        mock_evrq.realtimeOnly.assert_called_once()
        mock_evrq.setMaxResults.assert_called_once_with(1000)

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_no_optional_filters(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr_multi(
            sessionId=1, evrNames=[], eventIds=[], evrLevels=[],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_evrq.addEvrName.assert_not_called()
        mock_evrq.addEventId.assert_not_called()
        mock_evrq.addEvrLevel.assert_not_called()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_default_timeout_used(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_lad_client = MagicMock()
        mock_client.LadClient.return_value = mock_lad_client
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr_multi(
            sessionId=1, startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_lad_client.fetchEvrs.assert_called_once()
        call_kwargs = mock_lad_client.fetchEvrs.call_args
        assert call_kwargs[1]['timeout'] == lad_query._LAD_TIMEOUT_SEC

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_custom_timeout_propagated(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_lad_client = MagicMock()
        mock_client.LadClient.return_value = mock_lad_client
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr_multi(
            sessionId=1, startTime='2024-100T12:00:00',
            endTime='2024-100T13:00:00', timeout=300
        )

        call_kwargs = mock_lad_client.fetchEvrs.call_args
        assert call_kwargs[1]['timeout'] == 300

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_returns_flattened_response(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_client.LadClient.return_value = MagicMock()
        expected = [{'evrName': 'TEST_EVR'}]
        mock_gdsclient.flattenDict.return_value = expected

        result = lad_query.lad_get_evr_multi(
            sessionId=1, startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        assert result == expected


class TestLadGetEhaMulti:
    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_builds_correct_query(self, mock_client, mock_gdsclient):
        mock_ehaq = MagicMock()
        mock_client.ChanValQuery.return_value = mock_ehaq
        mock_lad_client = MagicMock()
        mock_client.LadClient.return_value = mock_lad_client
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_eha_multi(
            sessionId=1, channelIds=['CH-0001', 'CH-0002'],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00',
            timeout=120
        )

        assert mock_ehaq.addChannelId.call_count == 2
        mock_ehaq.addChannelId.assert_any_call('CH-0001')
        mock_ehaq.addChannelId.assert_any_call('CH-0002')
        mock_ehaq.useErt.assert_called_once()
        mock_ehaq.before.assert_called_once_with('2024-100T13:00:00')
        mock_ehaq.after.assert_called_once_with('2024-100T12:00:00')
        mock_ehaq.addSessionNumber.assert_called_once_with(1)
        mock_ehaq.realtimeOnly.assert_called_once()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_scet_time_type(self, mock_client, mock_gdsclient):
        mock_ehaq = MagicMock()
        mock_client.ChanValQuery.return_value = mock_ehaq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_eha_multi(
            sessionId=1, channelIds=['CH-0001'],
            timeType=TimeType.SCET,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_ehaq.useScet.assert_called_once()
        mock_ehaq.useErt.assert_not_called()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_sclk_time_type(self, mock_client, mock_gdsclient):
        mock_ehaq = MagicMock()
        mock_client.ChanValQuery.return_value = mock_ehaq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_eha_multi(
            sessionId=1, channelIds=['CH-0001'],
            timeType=TimeType.SCLK,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_ehaq.useSclk.assert_called_once()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_default_timeout(self, mock_client, mock_gdsclient):
        mock_ehaq = MagicMock()
        mock_client.ChanValQuery.return_value = mock_ehaq
        mock_lad_client = MagicMock()
        mock_client.LadClient.return_value = mock_lad_client
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_eha_multi(
            sessionId=1, channelIds=['CH-0001'],
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        call_kwargs = mock_lad_client.fetchChannels.call_args
        assert call_kwargs[1]['timeout'] == lad_query._LAD_TIMEOUT_SEC


class TestLadGetEvr:
    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_single_evr_query(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr(
            sessionId=1, evrName='EVR_A', eventId=100,
            evrLevel='ACTIVITY', timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_evrq.addEvrName.assert_called_once_with('EVR_A')
        mock_evrq.addEventId.assert_called_once_with(100)
        mock_evrq.addEvrLevel.assert_called_once_with('ACTIVITY')
        mock_evrq.useErt.assert_called_once()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_scet_time_type(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr(
            sessionId=1, timeType=TimeType.SCET,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_evrq.useScet.assert_called_once()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_sclk_time_type(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr(
            sessionId=1, timeType=TimeType.SCLK,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_evrq.useSclk.assert_called_once()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_none_filters_skipped(self, mock_client, mock_gdsclient):
        mock_evrq = MagicMock()
        mock_client.EvrQuery.return_value = mock_evrq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_evr(
            sessionId=1, evrName=None, eventId=None, evrLevel=None,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_evrq.addEvrName.assert_not_called()
        mock_evrq.addEventId.assert_not_called()
        mock_evrq.addEvrLevel.assert_not_called()


class TestLadGetEha:
    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_single_channel_query(self, mock_client, mock_gdsclient):
        mock_ehaq = MagicMock()
        mock_client.ChanValQuery.return_value = mock_ehaq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_eha(
            sessionId=1, channelId='CH-0001',
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_ehaq.addChannelId.assert_called_once_with('CH-0001')
        mock_ehaq.useErt.assert_called_once()
        mock_ehaq.addSessionNumber.assert_called_once_with(1)
        mock_ehaq.realtimeOnly.assert_called_once()

    @patch('core.lad_query.gdsclient')
    @patch('core.lad_query.client')
    def test_none_channel_skipped(self, mock_client, mock_gdsclient):
        mock_ehaq = MagicMock()
        mock_client.ChanValQuery.return_value = mock_ehaq
        mock_client.LadClient.return_value = MagicMock()
        mock_gdsclient.flattenDict.return_value = []

        lad_query.lad_get_eha(
            sessionId=1, channelId=None,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )

        mock_ehaq.addChannelId.assert_not_called()


class TestGetLadHttpsProtocol:
    @patch.dict('os.environ', {'LAD_HTTPS': 'true'})
    def test_true(self):
        assert lad_query.get_lad_https_protocol() is True

    @patch.dict('os.environ', {'LAD_HTTPS': 'True'})
    def test_true_capitalized(self):
        assert lad_query.get_lad_https_protocol() is True

    @patch.dict('os.environ', {'LAD_HTTPS': 'false'})
    def test_false(self):
        assert lad_query.get_lad_https_protocol() is False

    @patch.dict('os.environ', {'LAD_HTTPS': ''})
    def test_empty(self):
        assert lad_query.get_lad_https_protocol() is False
