from pydantic import BaseModel, Field
from typing import List
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
