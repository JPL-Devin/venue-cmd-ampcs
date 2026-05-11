"""Tests for Pydantic models in core/schema.py"""

import pytest
from pydantic import ValidationError

from core.schema import (
    DefaultCmdString, HealthStatusEnum, HealthStatus, ErrorResponse,
    MtakStartBodyModel, MtakStartResponse, StringSelection,
    FswCmdBodyModel, CmdDispatchedResp, HwCmdBodyModel, SseCmdBodyModel,
    BinaryFileBodyModel, ScmfFileBodyModel,
    EvrRtMultiBodyModel, TimeType, EVRObjectResp,
    ChannelValueObjectRespModel, EhaRtMultiBodyModel,
    DataPathMappingModel, MtakSessionEntry
)


class TestDefaultCmdString:
    def test_valid_values(self):
        assert DefaultCmdString.A.value == 'A'
        assert DefaultCmdString.B.value == 'B'
        assert DefaultCmdString.AB.value == 'AB'

    def test_from_value(self):
        assert DefaultCmdString('A') == DefaultCmdString.A


class TestHealthStatus:
    def test_ok_status(self):
        hs = HealthStatus(status=HealthStatusEnum.OK, message='')
        assert hs.status == HealthStatusEnum.OK
        assert hs.message == ''

    def test_error_status(self):
        hs = HealthStatus(status=HealthStatusEnum.ERROR, message='something broke')
        assert hs.status == HealthStatusEnum.ERROR
        assert hs.message == 'something broke'

    def test_missing_fields_raises(self):
        with pytest.raises(ValidationError):
            HealthStatus()


class TestErrorResponse:
    def test_default_message(self):
        er = ErrorResponse()
        assert er.message == ''

    def test_custom_message(self):
        er = ErrorResponse(message='test error')
        assert er.message == 'test error'


class TestMtakStartBodyModel:
    def test_minimal_valid(self):
        body = MtakStartBodyModel(sessions=[{'sessionId': 1}])
        assert len(body.sessions) == 1
        assert body.sessions[0].sessionId == 1
        assert body.sessions[0].dataPath is None
        assert body.timeout == 30
        assert body.defaultCmdString == DefaultCmdString.AB

    def test_custom_values(self):
        body = MtakStartBodyModel(
            sessions=[{'sessionId': 1}, {'dataPath': 'dp-alpha'}],
            timeout=60,
            defaultCmdString='A'
        )
        assert len(body.sessions) == 2
        assert body.sessions[0].sessionId == 1
        assert body.sessions[1].dataPath == 'dp-alpha'
        assert body.timeout == 60
        assert body.defaultCmdString == DefaultCmdString.A

    def test_timeout_below_minimum_raises(self):
        with pytest.raises(ValidationError):
            MtakStartBodyModel(sessions=[{'sessionId': 1}], timeout=10)

    def test_missing_sessions_raises(self):
        with pytest.raises(ValidationError):
            MtakStartBodyModel()

    def test_entry_with_both_raises(self):
        with pytest.raises(ValidationError):
            MtakStartBodyModel(sessions=[{'sessionId': 1, 'dataPath': 'dp-alpha'}])

    def test_entry_with_neither_raises(self):
        with pytest.raises(ValidationError):
            MtakStartBodyModel(sessions=[{}])


class TestDataPathMappingModel:
    def test_valid(self):
        m = DataPathMappingModel(dataPath='dp-alpha', sessionId=42)
        assert m.dataPath == 'dp-alpha'
        assert m.sessionId == 42

    def test_missing_data_path_raises(self):
        with pytest.raises(ValidationError):
            DataPathMappingModel(sessionId=1)

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            DataPathMappingModel(dataPath='dp')

    def test_wrong_session_id_type_raises(self):
        with pytest.raises(ValidationError):
            DataPathMappingModel(dataPath='dp', sessionId='not-an-int')


class TestMtakSessionEntry:
    def test_session_id_only(self):
        e = MtakSessionEntry(sessionId=1)
        assert e.sessionId == 1
        assert e.dataPath is None

    def test_data_path_only(self):
        e = MtakSessionEntry(dataPath='dp-alpha')
        assert e.sessionId is None
        assert e.dataPath == 'dp-alpha'

    def test_both_raises(self):
        with pytest.raises(ValidationError):
            MtakSessionEntry(sessionId=1, dataPath='dp-alpha')

    def test_neither_raises(self):
        with pytest.raises(ValidationError):
            MtakSessionEntry()


class TestMtakStartResponse:
    def test_valid(self):
        resp = MtakStartResponse(sessionIds=[1], startTime='2024-04-10T12:00:00.000Z')
        assert resp.sessionIds == [1]
        assert resp.startTime == '2024-04-10T12:00:00.000Z'


class TestStringSelection:
    def test_valid_values(self):
        assert StringSelection.DEFAULT.value == 'DEFAULT'
        assert StringSelection.A.value == 'A'
        assert StringSelection.B.value == 'B'
        assert StringSelection.AB.value == 'AB'


class TestFswCmdBodyModel:
    def test_minimal_valid(self):
        body = FswCmdBodyModel(sessionId=1, commandString='CMD_NO_OP')
        assert body.sessionId == 1
        assert body.dataPath is None
        assert body.commandString == 'CMD_NO_OP'
        assert body.validate_ is True
        assert body.stringSelection == StringSelection.DEFAULT
        assert body.timeout == 10

    def test_with_data_path(self):
        body = FswCmdBodyModel(dataPath='dp-alpha', commandString='CMD_NO_OP')
        assert body.sessionId is None
        assert body.dataPath == 'dp-alpha'

    def test_both_raises(self):
        with pytest.raises(ValidationError):
            FswCmdBodyModel(sessionId=1, dataPath='dp', commandString='CMD_NO_OP')

    def test_neither_raises(self):
        with pytest.raises(ValidationError):
            FswCmdBodyModel(commandString='CMD_NO_OP')

    def test_validate_alias(self):
        body = FswCmdBodyModel(**{'sessionId': 1, 'commandString': 'CMD_NO_OP', 'validate': False})
        assert body.validate_ is False

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            FswCmdBodyModel(sessionId=1)

    def test_timeout_negative_raises(self):
        with pytest.raises(ValidationError):
            FswCmdBodyModel(sessionId=1, commandString='CMD_NO_OP', timeout=-1)


class TestHwCmdBodyModel:
    def test_minimal_valid(self):
        body = HwCmdBodyModel(sessionId=1, commandStem='HW_CMD_STEM')
        assert body.sessionId == 1
        assert body.commandStem == 'HW_CMD_STEM'
        assert body.stringSelection == StringSelection.DEFAULT
        assert body.timeout == 10

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            HwCmdBodyModel(sessionId=1)


class TestSseCmdBodyModel:
    def test_minimal_valid(self):
        body = SseCmdBodyModel(sessionId=1, commandString='SSE_CMD')
        assert body.sessionId == 1
        assert body.commandString == 'SSE_CMD'
        assert body.timeout == 10


class TestBinaryFileBodyModel:
    def test_minimal_valid(self):
        body = BinaryFileBodyModel(
            sessionId=1,
            sourceFilePath='/path/to/file.bin',
            targetFilePath='/eng1/file.bin',
            fileType=1
        )
        assert body.sessionId == 1
        assert body.sourceFilePath == '/path/to/file.bin'
        assert body.targetFilePath == '/eng1/file.bin'
        assert body.overwrite is True
        assert body.fileType == 1
        assert body.stringSelection == StringSelection.DEFAULT

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            BinaryFileBodyModel(sessionId=1, sourceFilePath='/path')


class TestScmfFileBodyModel:
    def test_minimal_valid(self):
        body = ScmfFileBodyModel(sessionId=1, filePath='/path/to/file.scmf')
        assert body.sessionId == 1
        assert body.filePath == '/path/to/file.scmf'
        assert body.disableChecks is False
        assert body.timeout == 10

    def test_disable_checks(self):
        body = ScmfFileBodyModel(sessionId=1, filePath='/path', disableChecks=True)
        assert body.disableChecks is True


class TestCmdDispatchedResp:
    def test_defaults(self):
        resp = CmdDispatchedResp()
        assert resp.cmdRequested == ''
        assert resp.dispatchTime == ''

    def test_custom(self):
        resp = CmdDispatchedResp(cmdRequested='CMD_NO_OP', dispatchTime='2024-04-10T12:00:00.000Z')
        assert resp.cmdRequested == 'CMD_NO_OP'


class TestTimeType:
    def test_values(self):
        assert TimeType.ERT.value == 'ERT'
        assert TimeType.SCET.value == 'SCET'
        assert TimeType.SCLK.value == 'SCLK'


class TestEvrRtMultiBodyModel:
    def test_minimal_valid(self):
        body = EvrRtMultiBodyModel(
            sessionId=1,
            startTime='2024-100T12:00:00',
            endTime='2024-100T13:00:00'
        )
        assert body.sessionId == 1
        assert body.evrNames == []
        assert body.eventIds == []
        assert body.evrLevels == []
        assert body.timeout == 240

    def test_full_valid(self):
        body = EvrRtMultiBodyModel(
            sessionId=1,
            evrNames=['EVR_A', 'EVR_B'],
            eventIds=[100, 200],
            evrLevels=['ACTIVITY', 'DIAGNOSTIC'],
            startTime='2024-100T12:00:00',
            endTime='2024-100T13:00:00',
            timeout=120
        )
        assert len(body.evrNames) == 2
        assert len(body.eventIds) == 2

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            EvrRtMultiBodyModel(sessionId=1)


class TestEVRObjectResp:
    def test_defaults(self):
        resp = EVRObjectResp()
        assert resp.evrName == ''
        assert resp.sessionId == 0
        assert resp.vcId == 0
        assert resp.fromSSE is False
        assert resp.isRecorded is False


class TestChannelValueObjectRespModel:
    def test_defaults(self):
        resp = ChannelValueObjectRespModel()
        assert resp.dn == ''
        assert resp.eu == 0.0
        assert resp.channelId == ''
        assert resp.isRecorded is False
        assert resp.dnAlarmState == ''
        assert resp.euAlarmState == ''


class TestEhaRtMultiBodyModel:
    def test_with_session_id(self):
        body = EhaRtMultiBodyModel(
            sessionId=1,
            channelIds=['CH-0001'],
            startTime='2024-100T12:00:00',
            endTime='2024-100T13:00:00'
        )
        assert body.sessionId == 1
        assert body.dataPath is None
        assert body.channelIds == ['CH-0001']
        assert body.timeout == 240

    def test_with_data_path(self):
        body = EhaRtMultiBodyModel(
            dataPath='dp-alpha',
            channelIds=['CH-0001'],
            startTime='2024-100T12:00:00',
            endTime='2024-100T13:00:00'
        )
        assert body.sessionId is None
        assert body.dataPath == 'dp-alpha'

    def test_neither_raises(self):
        with pytest.raises(ValidationError):
            EhaRtMultiBodyModel(
                channelIds=['CH-0001'],
                startTime='2024-100T12:00:00',
                endTime='2024-100T13:00:00'
            )

    def test_both_raises(self):
        with pytest.raises(ValidationError):
            EhaRtMultiBodyModel(
                sessionId=1,
                dataPath='dp-alpha',
                channelIds=['CH-0001'],
                startTime='2024-100T12:00:00',
                endTime='2024-100T13:00:00'
            )

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            EhaRtMultiBodyModel(startTime='2024-100T12:00:00', endTime='2024-100T13:00:00')
