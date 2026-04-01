from pydantic import BaseModel, Field
from typing import List, Union
from enum import Enum

class DefaultCmdString(str, Enum):
    A = 'A'
    B = 'B'
    AB = 'AB'

class HealthStatusEnum(str, Enum):
    OK = 'OK'
    ERROR = 'ERROR'
    UNKNOWN = 'UNKNOWN'

class HealthStatus(BaseModel):
    status: HealthStatusEnum = Field(description='health status')
    message: str = Field(description='status message')

class ErrorResponse(BaseModel):
    message: str = Field('', description='Error message')

class MtakStartBodyModel(BaseModel):
    sessionIds: List[int] = Field(description='AMPCS session ids to start MTAK on')
    timeout: int = Field(30, ge=25,
        description='How long to wait until timeout in seconds. The minimum is 25 seconds since MTAK takes some time to start')
    defaultCmdString: DefaultCmdString = Field(DefaultCmdString.AB, 
        description='Which sides of flight computer the command is for. This will be used if default is used for stringSelection.')

class MtakStartResponse(BaseModel):
    sessionIds: List[int] = Field(description='AMPCS session ids')
    startTime: str = Field(description='Time that MTAK started')

class StringSelection(str, Enum):
    DEFAULT = 'DEFAULT'
    A = 'A'
    B = 'B'
    AB = 'AB'

class FswCmdBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to send the command through')
    commandString: str = Field(description='The command string including the command stem and any arguments')
    # need to prepend underscore to avoid name conflict with built-in property of Pydantic
    validate_: bool = Field(True, alias='validate', 
        description='Flag for AMPCS to validate the command against the FSW dict before radiating')
    stringSelection: StringSelection = Field(StringSelection.DEFAULT,
        description='Which sides of flight computer the command is for')
    timeout: int = Field(10, ge=0, description='The timeout on the dispatch process in seconds')

class CmdDispatchedResp(BaseModel):
    cmdRequested: str = Field('', 
        description='This mirrors what was received as the requested command string')
    # time format was checked
    dispatchTime: str = Field('', 
        description='Time that the dispatch occurred. Example: 2017-09-25T03:57:42.676Z') 

class HwCmdBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to send this file through')
    commandStem: str = Field(description='The command stem of the HW Command')
    stringSelection: StringSelection = Field(StringSelection.DEFAULT, 
        description='Specifies the MTAK string to send the command')
    timeout: int = Field(10, ge=0, 
        description='The timeout on the dispatch process in seconds')

class SseCmdBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to send the command through')
    commandString: str = Field(description='The command string including the command stem and any arguments')
    timeout: int = Field(10, ge=0, description='The timeout on the dispatch process in seconds')

class BinaryFileBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to send the command through')
    sourceFilePath: str = Field(description='The full path on GDS host (ex: /proj/europa/sit/current/files/myfile.data)')
    targetFilePath: str = Field(description='The full onboard path (i.e. /eng1/myfile.data')
    overwrite: bool = Field(True, description='if True will overwrite any existing onboard file')
    fileType: int = Field(description='The file type that should be used to build the binary file into a SCMF')
    stringSelection: StringSelection = Field(StringSelection.DEFAULT, 
        description='Specifies the MTAK string to send the command')
    timeout: int = Field(10, ge=0, 
        description='The timeout on the dispatch process in seconds')

class ScmfFileBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to send the command through')
    filePath: str = Field(description='The full path on GDS host (ex: /proj/europa/sit/current/files/myfile.scmf)')
    disableChecks: bool = Field(False, description='Disables the check done by AMPCS for invalid scmf file')
    timeout: int = Field(10, ge=0, description='The timeout on the dispatch process in seconds')

class EvrRtBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to qury against')
    # wild card works
    evrName: Union[str, None] = Field(None, description='Name of EVRs to query. Wildcard * can be used.')
    eventId: Union[int, None] = Field(None, description='EVR event ID')
    evrLevel: Union[str, None] = Field(None, 
        description='Filter by EVR level. Wildcard * can be used. Note that EVR levels are project specific.')
    startTime: str = Field(description='Query start time in ERT DOY UTC (2009-202T12:35:00)')
    endTime: str = Field(description='Query end time in ERT DOY UTC (2009-202T12:35:00)')
    timeout: int = Field(240, ge=0, description='How long to wait in seconds for results to return')

class EvrRtMultiBodyModel(BaseModel):
    sessionId: int = Field(description='The AMPCS session to qury against')
    # wild card works
    evrNames: List[str] = Field([], 
        description='Name of EVRs to retrieve. No wildcard is supported')
    eventIds: List[int] = Field([], 
        description='Event IDs of EVRs to retreive')
    evrLevels: List[str] = Field([], 
        description='Levels of EVRs to return. Note that levels are project specific.')
    startTime: str = Field(description='Query start time in ERT DOY UTC (2009-202T12:35:00)')
    endTime: str = Field(description='Query end time in ERT DOY UTC (2009-202T12:35:00)')
    timeout: int = Field(240, ge=0, description='How long to wait in seconds for results to return')

class TimeType(str, Enum):
    ERT = 'ERT'
    SCET = 'SCET'
    SCLK = 'SCLK'

class EVRObjectResp(BaseModel):
    evrName: str = Field('', description='Name of the EVR')
    sessionId: int = Field(0, description='The AMPCS session ID')
    vcId: int = Field(0, description='The virtual channel ID')
    eventId: int = Field(0, description='EVR event ID')
    evrLevel: str = Field('', description='Level of EVR')
    fromSSE: bool = Field(False, description='True if EVR is frome SSE, false otherwise')
    evrMessage: str = Field('', description='Message that this EVR contains')
    evrModule: str = Field('', description='FSW module that generated this EVR')
    sclk: str = Field('', description='SCLK for this EVR')  # sclk is a string in response
    ert: str = Field('', description='Earth received (ISO-formatted) time')
    scet: str = Field('', description='ISO-formatted spacecraft event time')
    isRecorded: bool = Field(False, description='True if this is a recorded EVR (from data products)')

class ChannelValueObjectRespModel(BaseModel):
    dn: str = Field('', description='Data number value. Only returns string for now')
    eu: float = Field(0.0, description='Engineering unit value')
    channelId: str = Field('', description='The Id of the EHA channel')
    sessionId: int = Field(0, description='The AMPCS session ID that the result came from')
    vcId: int = Field(0, description='The virtual channel ID that the result came from')
    channelName: str = Field('', description='The name of the EHA channel')
    channelType: str = Field('', description='The type of the EHA channel')
    channelStatus: str = Field('', description='The string status of the channel if it is a table-driven channel (only for boolean and status type channels)')
    sclk: str = Field('', description='SCLK when this value was read')   # sclk is a string in response
    ert: str = Field('', description='Earth received (ISO-formatted) time when this value was received')
    scet: str = Field('', description='Correlated SCLK time in ISO format')
    isRecorded: bool = Field(False, description='True if this is a recorded EHA, false otherwise')
    dnAlarmState: str = Field('', description='Indicates if the channel measurement is in alarm (on DN values)')
    euAlarmState: str = Field('', description='Indicates if the channel measurement is in alarm (on EU values)')

class EhaRtBodyModel(BaseModel):
    sessionId: Union[int, None] = Field(None, description='The AMPCS session to query against')
    channelId: Union[str, None] = Field(None, description='The channel ID to search for')
    # startTime is required
    startTime: str = Field(description='Query start time in ERT DOY UTC (2009-202T12:35:00)')
    # endTime is required
    endTime: str = Field(description='Query end time in ERT DOY UTC (2009-202T12:35:00)')
    timeout: int = Field(240, ge=0, description='How long to wait in seconds for results to return')

class EhaRtMultiBodyModel(BaseModel):
    sessionId: Union[int, None] = Field(None, description='The AMPCS session to query against')
    channelIds: List[str] = Field(description='The channel IDs to search for')
    # startTime is required
    startTime: str = Field(description='Query start time in ERT DOY UTC (2009-202T12:35:00)')
    # endTime is required
    endTime: str = Field(description='Query end time in ERT DOY UTC (2009-202T12:35:00)')
    timeout: int = Field(240, ge=0, description='How long to wait in seconds for results to return')
