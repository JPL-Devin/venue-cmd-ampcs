"""Tests for business logic in core/venue_core.py with mocked dependencies."""

import pytest
from unittest.mock import patch, MagicMock

from core.schema import TimeType
from core import venue_core


class TestCheckSessionId:
    def test_valid_int(self):
        venue_core.checkSessionId(1)

    def test_string_raises(self):
        with pytest.raises(ValueError, match='Invalid sessionId'):
            venue_core.checkSessionId('abc')

    def test_none_raises(self):
        with pytest.raises(ValueError, match='Invalid sessionId'):
            venue_core.checkSessionId(None)

    def test_float_raises(self):
        with pytest.raises(ValueError, match='Invalid sessionId'):
            venue_core.checkSessionId(1.5)


class TestGetEvrDict:
    def test_returns_correct_keys(self):
        result = venue_core.get_evr_dict(
            sessionId=1, eventId=100, vcId=0, evrName='TEST_EVR',
            evrLevel='ACTIVITY', fromSSE=False, evrMessage='test message',
            evrModule='MOD', sclk='0001234-56789', ert='2024-04-10T12:00:00.000Z',
            scet='2024-04-10T11:59:50.000Z', isRecorded=False
        )
        assert result['sessionId'] == 1
        assert result['eventId'] == 100
        assert result['evrName'] == 'TEST_EVR'
        assert result['evrLevel'] == 'ACTIVITY'
        assert result['fromSSE'] is False
        assert result['evrMessage'] == 'test message'
        assert result['isRecorded'] is False

    def test_invalid_session_id_raises(self):
        with pytest.raises(ValueError):
            venue_core.get_evr_dict(
                sessionId='bad', eventId=100, vcId=0, evrName='TEST',
                evrLevel='ACTIVITY', fromSSE=False, evrMessage='msg',
                evrModule=None, sclk='0', ert='t', scet='t', isRecorded=False
            )


class TestGetEhaDict:
    def test_returns_correct_keys(self):
        result = venue_core.get_eha_dict(
            sessionId=1, channelId='CH-0001', dn='42', eu=42.0,
            vcId=0, channelName='TEST_CHAN', channelType='DN',
            channelStatus='', dnAlarmState='NONE', euAlarmState='NONE',
            sclk='0001234-56789', ert='2024-04-10T12:00:00.000Z',
            scet='2024-04-10T11:59:50.000Z', isRecorded=False
        )
        assert result['sessionId'] == 1
        assert result['channelId'] == 'CH-0001'
        assert result['dn'] == '42'
        assert result['eu'] == 42.0


class TestCoreStartMtak:
    @patch('core.venue_core.mtak_startup_timeout')
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_success(self, mock_time, mock_mtak):
        mock_mtak.return_value = None
        session_ids, start_time = venue_core.core_start_mtak(
            sessionIds=[1], defaultCmdString='AB', timeout=30
        )
        assert session_ids == [1]
        assert start_time == '2024-04-10T12:00:00.000Z'
        mock_mtak.assert_called_once_with(sessionIds=[1], defaultCmdString='AB', timeout_sec=30)

    @patch('core.venue_core.mtak_startup_timeout', side_effect=Exception('MTAK failed'))
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_mtak_exception_propagates(self, mock_time, mock_mtak):
        with pytest.raises(Exception, match='MTAK failed'):
            venue_core.core_start_mtak(sessionIds=[1], defaultCmdString='AB', timeout=30)


class TestCoreStopMtak:
    @patch('core.venue_core.mtak_shutdown')
    def test_success(self, mock_shutdown):
        result = venue_core.core_stop_mtak()
        assert result == ''
        mock_shutdown.assert_called_once()

    @patch('core.venue_core.mtak_shutdown', side_effect=Exception('shutdown failed'))
    def test_exception_propagates(self, mock_shutdown):
        with pytest.raises(Exception, match='shutdown failed'):
            venue_core.core_stop_mtak()


class TestCoreSendFswCmd:
    @patch('core.venue_core.mtak_send_fsw_cmd')
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_success(self, mock_time, mock_send):
        mock_send.return_value = None
        cmd, dispatch_time = venue_core.core_send_fsw_cmd(
            sessionId=1, cmdString='CMD_NO_OP', validate=True,
            stringSelection='AB', timeout=10
        )
        assert cmd == 'CMD_NO_OP'
        assert dispatch_time == '2024-04-10T12:00:00.000Z'

    @patch('core.venue_core.mtak_send_fsw_cmd', side_effect=Exception('cmd failed'))
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_exception_propagates(self, mock_time, mock_send):
        with pytest.raises(Exception, match='cmd failed'):
            venue_core.core_send_fsw_cmd(
                sessionId=1, cmdString='CMD_NO_OP', validate=True,
                stringSelection='AB', timeout=10
            )


class TestCoreSendHwCmd:
    @patch('core.venue_core.mtak_send_hw_cmd')
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_success(self, mock_time, mock_send):
        mock_send.return_value = None
        cmd, dispatch_time = venue_core.core_send_hw_cmd(
            sessionId=1, cmdStem='HW_CMD', stringSelection='A', timeout=10
        )
        assert cmd == 'HW_CMD'
        assert dispatch_time == '2024-04-10T12:00:00.000Z'


class TestCoreSendSseCmd:
    @patch('core.venue_core.mtak_send_sse_cmd')
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_success(self, mock_time, mock_send):
        mock_send.return_value = None
        cmd, dispatch_time = venue_core.core_send_sse_cmd(
            sessionId=1, cmdString='SSE_CMD', timeout=10
        )
        assert cmd == 'SSE_CMD'
        assert dispatch_time == '2024-04-10T12:00:00.000Z'


class TestCoreSendFswFile:
    @patch('core.venue_core.mtak_send_fsw_file')
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_success(self, mock_time, mock_send):
        mock_send.return_value = None
        cmd, dispatch_time = venue_core.core_send_fsw_file(
            sessionId=1, sourcePath='/src/file.bin', targetLoc='/eng1/file.bin',
            fileType=1, overwrite=True, stringSelection='AB', timeout=10
        )
        assert 'sourcePath: /src/file.bin' in cmd
        assert dispatch_time == '2024-04-10T12:00:00.000Z'


class TestCoreSendScmfFile:
    @patch('core.venue_core.mtak_send_scmf_file')
    @patch('core.venue_core.get_now_isoZ', return_value='2024-04-10T12:00:00.000Z')
    def test_success(self, mock_time, mock_send):
        mock_send.return_value = None
        cmd, dispatch_time = venue_core.core_send_scmf_file(
            sessionId=1, filePath='/path/file.scmf', disableChecks=False, timeout=10
        )
        assert 'SCMF: /path/file.scmf' in cmd
        assert dispatch_time == '2024-04-10T12:00:00.000Z'


class TestGetRtEvrMulti:
    @patch('core.venue_core.lad_query')
    def test_success_with_evrs(self, mock_lad):
        mock_lad.lad_get_evr_multi.return_value = [
            {
                'sessionNumber': '1', 'evrId': '100', 'vcid': '0',
                'evrName': 'CMD_SVC_EVR_CMD_COMPLETED_SUCCESS', 'evrLevel': 'ACTIVITY',
                'isFsw': 'true', 'message': 'Command completed', 'sclk': '0001234567-12345',
                'ert': '2024-100T12:00:00.000000', 'scet': '2024-100T11:59:50.000000',
                'isRealTime': 'true'
            }
        ]
        result = venue_core.get_rt_evr_multi(
            sessionId=1, timeout=60,
            evrNames=['CMD_SVC_EVR_CMD_COMPLETED_SUCCESS'],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )
        assert len(result) == 1
        assert result[0]['evrName'] == 'CMD_SVC_EVR_CMD_COMPLETED_SUCCESS'
        assert result[0]['fromSSE'] is False
        assert result[0]['ert'].endswith('Z')
        assert result[0]['isRecorded'] is False

    @patch('core.venue_core.lad_query')
    def test_empty_results(self, mock_lad):
        mock_lad.lad_get_evr_multi.return_value = []
        result = venue_core.get_rt_evr_multi(
            sessionId=1, timeout=60, timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )
        assert result == []

    def test_invalid_time_format_raises(self):
        with pytest.raises(Exception, match='Expected DOY format'):
            venue_core.get_rt_evr_multi(
                sessionId=1, timeout=60, timeType=TimeType.ERT,
                startTime='2024-04-10T12:00:00', endTime='2024-04-10T13:00:00'
            )

    def test_start_after_end_raises(self):
        with pytest.raises(Exception, match='startTime is after endTime'):
            venue_core.get_rt_evr_multi(
                sessionId=1, timeout=60, timeType=TimeType.ERT,
                startTime='2024-100T14:00:00', endTime='2024-100T13:00:00'
            )

    @patch('core.venue_core.lad_query')
    def test_lad_error_raises(self, mock_lad):
        mock_lad.lad_get_evr_multi.side_effect = Exception('LAD connection failed')
        with pytest.raises(Exception, match='Error when querying evrs'):
            venue_core.get_rt_evr_multi(
                sessionId=1, timeout=60, timeType=TimeType.ERT,
                startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
            )

    @patch('core.venue_core.lad_query')
    def test_sse_evr_detected(self, mock_lad):
        mock_lad.lad_get_evr_multi.return_value = [
            {
                'sessionNumber': '1', 'evrId': '200', 'vcid': '',
                'evrName': 'SSE_EVR', 'evrLevel': 'DIAGNOSTIC',
                'isFsw': 'false', 'message': 'SSE event', 'sclk': '0',
                'ert': '2024-100T12:00:00.000000', 'scet': '2024-100T12:00:00.000000',
                'isRealTime': 'false'
            }
        ]
        result = venue_core.get_rt_evr_multi(
            sessionId=1, timeout=60, timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )
        assert result[0]['fromSSE'] is True
        assert result[0]['vcId'] is None
        assert result[0]['isRecorded'] is True


class TestGetRtEhaMulti:
    @patch('core.venue_core.lad_query')
    def test_success_with_channels(self, mock_lad):
        mock_lad.lad_get_eha_multi.return_value = [
            {
                'sessionNumber': '1', 'channelId': 'CH-0001', 'dn': '42',
                'eu': '42.0', 'vcid': '0', 'channelType': 'DN',
                'status': '', 'dnAlarmLevel': 'NONE', 'euAlarmLevel': 'NONE',
                'sclk': '0001234567-12345',
                'ert': '2024-100T12:00:00.000000', 'scet': '2024-100T11:59:50.000000',
                'isRealTime': 'true'
            }
        ]
        result = venue_core.get_rt_eha_multi(
            sessionId=1, timeout=60, channelIds=['CH-0001'],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )
        assert len(result) == 1
        assert result[0]['channelId'] == 'CH-0001'
        assert result[0]['dn'] == '42'
        assert result[0]['eu'] == 42.0
        assert result[0]['ert'].endswith('Z')

    @patch('core.venue_core.lad_query')
    def test_empty_results(self, mock_lad):
        mock_lad.lad_get_eha_multi.return_value = []
        result = venue_core.get_rt_eha_multi(
            sessionId=1, timeout=60, channelIds=['CH-0001'],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )
        assert result == []

    def test_invalid_time_format_raises(self):
        with pytest.raises(Exception, match='Expected DOY format'):
            venue_core.get_rt_eha_multi(
                sessionId=1, timeout=60, channelIds=['CH-0001'],
                timeType=TimeType.ERT,
                startTime='2024-04-10T12:00:00', endTime='2024-04-10T13:00:00'
            )

    def test_start_after_end_raises(self):
        with pytest.raises(Exception, match='startTime is after endTime'):
            venue_core.get_rt_eha_multi(
                sessionId=1, timeout=60, channelIds=['CH-0001'],
                timeType=TimeType.ERT,
                startTime='2024-100T14:00:00', endTime='2024-100T13:00:00'
            )

    @patch('core.venue_core.lad_query')
    def test_lad_error_raises(self, mock_lad):
        mock_lad.lad_get_eha_multi.side_effect = Exception('LAD connection failed')
        with pytest.raises(Exception, match='Error when querying channel values'):
            venue_core.get_rt_eha_multi(
                sessionId=1, timeout=60, channelIds=['CH-0001'],
                timeType=TimeType.ERT,
                startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
            )

    @patch('core.venue_core.lad_query')
    def test_empty_eu_and_vcid(self, mock_lad):
        mock_lad.lad_get_eha_multi.return_value = [
            {
                'sessionNumber': '1', 'channelId': 'CH-0001', 'dn': '0',
                'eu': '', 'vcid': '', 'channelType': 'DN',
                'status': '', 'dnAlarmLevel': 'NONE', 'euAlarmLevel': 'NONE',
                'sclk': '0',
                'ert': '2024-100T12:00:00.000000', 'scet': '2024-100T12:00:00.000000',
                'isRealTime': 'true'
            }
        ]
        result = venue_core.get_rt_eha_multi(
            sessionId=1, timeout=60, channelIds=['CH-0001'],
            timeType=TimeType.ERT,
            startTime='2024-100T12:00:00', endTime='2024-100T13:00:00'
        )
        assert result[0]['eu'] is None
        assert result[0]['vcId'] is None
