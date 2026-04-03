# import mtak first since this messes up logging
from .mtak_cmd import mtak_startup_timeout, mtak_shutdown, \
  mtak_send_fsw_cmd, mtak_send_hw_cmd, mtak_send_sse_cmd, \
  mtak_send_fsw_file, mtak_send_scmf_file

from typing import List, Dict

import logging
logger = logging.getLogger(__name__)

from datetime import datetime

import traceback
from .core_utils import str2bool, get_now_isoZ, doyToIsoZ, normalize_with_microsecs
from .schema import TimeType
from . import lad_query

def core_start_mtak (sessionIds, defaultCmdString, timeout):
  '''

  Launches uplink and downlink proxies

  :param sessionIds: session key/Id (int)
  :param timeout: how long to wait for mtak before exiting (int). Minimum 25 seconds
  :return: MTAK response per spec
  '''
  startTimeStr = get_now_isoZ()
  logger.info(f"SessionIds: {sessionIds}")
  mtak_startup_timeout(sessionIds=sessionIds,
                                defaultCmdString=defaultCmdString,
                                timeout_sec=timeout)
  
  return (sessionIds, startTimeStr)



def core_stop_mtak ():
  ''' Stops the uplink and downlink proxies '''

  logger.info(f"calling mtak_shutdown")
  mtak_shutdown()

  return ''

def core_send_fsw_cmd (sessionId, cmdString, validate, stringSelection, timeout=None):
  '''

  Sends flight software command using MTAK

  :param sessionId: session key for mpcs session to send fsw cmd to (int)
  :param cmdString: actual fsw cmd (string)
  :param timeout: amount of time (int)

  :return: (cmdString, dispatchTimeStr)

  '''
  dispatchTimeStr = get_now_isoZ()

  mtak_send_fsw_cmd(sessionId=sessionId,
                    cmdString=cmdString,
                    validate=validate,
                    stringSelection=stringSelection,
                    timeout_sec=timeout)
  return (cmdString, dispatchTimeStr)

def core_send_hw_cmd (sessionId, cmdStem, stringSelection, timeout=None):
  '''
  Sends hardware command using MTAK

  :param sessionId: session key for mpcs session to send fsw cmd to (int)
  :param cmdStem: actual hw cmd (string)
  :param timeout: amount of time (int)

  :return: (cmdStem, dispatchTimeStr)

  '''
  dispatchTimeStr = get_now_isoZ()

  mtak_send_hw_cmd(sessionId=sessionId,
                  cmdStem=cmdStem,
                  stringSelection=stringSelection,
                  timeout_sec=timeout)
  return (cmdStem, dispatchTimeStr)

def core_send_sse_cmd (sessionId, cmdString, timeout=None):
  '''
  Sends SSE command using MTAK

  :param sessionId: session key for mpcs to send sse cmd to (int)
  :param cmdString: actual sse cmd (string)
  :param socketPort: the socket to send data to (int)
  :param timeout: amount of time (int)

  :return: (cmdString, dispatchTimeStr)

  '''
  dispatchTimeStr = get_now_isoZ()

  mtak_send_sse_cmd(sessionId=sessionId,
                  cmdString=cmdString,
                  timeout_sec=timeout)
  return (cmdString, dispatchTimeStr)

def core_send_fsw_file (sessionId, sourcePath, targetLoc, fileType, overwrite, stringSelection, timeout=None):
  '''
  Sends FSW file using MTAK

  :param sessionId: AMPCS session to send this file through (int)
  :param sourcePath: full path on venue's file system to locate the file (string)
  :param targetLoc: full path on the vehicle's file system to send the file (string)
  :param fileType: file type to build binary file into SCMF (int)
  :param overwrite: True if this file should overwrite existing file in targetLoc (boolean)
  :param timeout: timeout on the dispatch process (int)

  :return: (cmdInfo, dispatchTimeStr)

  '''
  dispatchTimeStr = get_now_isoZ()

  mtak_send_fsw_file(sessionId=sessionId,
                          sourcePath=sourcePath,
                          targetLoc=targetLoc,
                          fileType=fileType,
                          overwrite=overwrite,
                          stringSelection=stringSelection,
                          timeout_sec=timeout)
  
  return (
    f'sourcePath: {sourcePath} targetLoc: {targetLoc} fileType: {fileType} overwrite: {overwrite}', 
    dispatchTimeStr
  )

def core_send_scmf_file(sessionId, filePath, disableChecks, timeout=None):
  '''

  Sends flight software SCMF file using MTAK

  :param sessionId: session key for mpcs session to send scmf file (integer)
  :param filePath: full path on venue's file system to file (string)
  :param disableChecks: disables AMPCS check of the scmf (boolean)
  :param timeout: timeout on the dispatch process (int)

  :return: (cmdInfo, dispatchTimeStr)

  '''
  dispatchTimeStr = get_now_isoZ()

  mtak_send_scmf_file(sessionId=sessionId,
                      filePath=filePath,
                      disableChecks=disableChecks,
                      timeout_sec=timeout)
  return (f'SCMF: {filePath} disableChecks: {disableChecks}', dispatchTimeStr)

def checkSessionId(sessionId):
  if (not isinstance(sessionId, int)):
    raise ValueError("Invalid sessionId. Should be an integer.")


def get_evr_dict(sessionId, eventId, vcId, evrName, evrLevel, fromSSE,
              evrMessage, evrModule, sclk, ert, scet, isRecorded):
  checkSessionId(sessionId)
  return {
    'sessionId': sessionId,
    'evrName': evrName,
    'vcId': vcId,
    'eventId': eventId,
    'evrLevel': evrLevel,
    'fromSSE': fromSSE,
    'evrMessage': evrMessage,
    'evrModule': evrModule,
    'sclk': sclk,
    'ert': ert,
    'scet': scet,
    'isRecorded': isRecorded
  }

def get_rt_evr_multi(sessionId: int, timeout: int, evrNames: List[str]=[], eventIds: List[int]=[],
              evrLevels: List[str]=[], timeType:TimeType=None, startTime=None,
              endTime=None) -> List[Dict]:
  '''
  Queries for EVR using GLAD client. More than one EVR name can be queried.
  Time format for all time types except SCLK (in GMT) is YYYY-DOYThh:mm:ss.ttt

  Parameters
  ------------------
  sessionId:
    AMPCS session id
  timeout:
    Time to wait in seconds before returning timeout
  evrNames:
    names of evrs to match. No wildcard is supported.
  eventIds:
    EVR event ids
  evrLevels:
    EVR levels
  timeType:
    Should be one of TimeType
  startTime:
    Begin time of query range
  endTime:
    End time of query range

  Returns:
  List[Dict]
    list of evrs in dict
  '''

  try:
    start_dt = datetime.strptime(startTime, '%Y-%jT%H:%M:%S')
    end_dt = datetime.strptime(endTime, '%Y-%jT%H:%M:%S')
  except ValueError as ex:
    msg = "Expected DOY format with integer seconds - ex:2017-310T19:27:13"
    logger.exception(msg)
    raise Exception(msg) from ex

  if (start_dt > end_dt):
    msg = "startTime is after endTime"
    raise Exception(msg)

  try:
    evrs = lad_query.lad_get_evr_multi(sessionId=sessionId, evrNames=evrNames,
                        eventIds=eventIds, evrLevels=evrLevels,
                        timeType=timeType, startTime=startTime,
                        endTime=endTime, timeout=timeout)
  except Exception as ex:
    msg = 'Error when querying evrs from GlobalLad'
    logger.error(traceback.format_exc())
    raise Exception(msg) from ex

  logger.info("Found %d EVR results from GlobalLad." %(len(evrs)))

  # convert data to format required by server spec
  evr_dicts = []

  for evr in evrs:
    evr_dict = get_evr_dict(sessionId=int(evr['sessionNumber']),
                  eventId=int(evr['evrId']),
                  vcId=(int(evr['vcid']) if (evr['vcid'] != "") else None),
                  evrName=str(evr['evrName']),
                  evrLevel=str(evr['evrLevel']),
                  fromSSE=(not str2bool(evr['isFsw'])),
                  evrMessage=str(evr['message']),
                  evrModule=None,
                  sclk=str(evr['sclk']),
                  ert=doyToIsoZ(normalize_with_microsecs(evr['ert'])),
                  scet=doyToIsoZ(normalize_with_microsecs(evr['scet'])),
                  isRecorded=(not str2bool(evr['isRealTime'])))
    evr_dicts.append(evr_dict)
  return evr_dicts

def get_eha_dict(sessionId, channelId, dn, eu, vcId, channelName,
              channelType, channelStatus, dnAlarmState, euAlarmState,
              sclk, ert, scet, isRecorded):
  return {
    'sessionId': sessionId,
    'channelId': channelId,
    'dn': dn,
    'eu': eu,
    'vcId': vcId,
    'channelName': channelName,
    'channelType': channelType,
    'channelStatus': channelStatus,
    'dnAlarmState': dnAlarmState,
    'euAlarmState': euAlarmState,
    'sclk': sclk,
    'ert': ert,
    'scet': scet,
    'isRecorded': isRecorded
  }

def get_rt_eha_multi(sessionId: int, timeout: int, channelIds: List[str]=[], timeType:TimeType=None, startTime: str=None,
                 endTime: str=None):
  '''
  Dispatches realtime eha query to globallad, validates output, and generates response
  based on spec for eha response

  Keyword arguments:
  sessionId -- AMPCS session id
  channelId  -- EHA channel ID (string)
  timeType -- Should be one of TimeType enum
  startTime -- Begin time of range (string)
  endTime  -- End time of range (string)
  timeout -- Internal timeout in seconds

  Time format for all time types except SCLK is YYYY-DOYThh:mm:ss.ttt

  Returns:
    list of ehas in dict

  '''
  eha_dicts = []

  try:
    start_dt = datetime.strptime(startTime, '%Y-%jT%H:%M:%S')
    end_dt = datetime.strptime(endTime, '%Y-%jT%H:%M:%S')
  except ValueError as ex:
    msg = 'Expected DOY format with integer seconds - ex:2017-310T19:27:13'
    logger.exception(msg)
    raise Exception(msg) from ex

  if (start_dt > end_dt):
    raise Exception('startTime is after endTime')

  try:
    ehas = lad_query.lad_get_eha_multi(sessionId=sessionId, channelIds=channelIds,
                        timeType=timeType, startTime=startTime,
                        endTime=endTime, timeout=timeout)
  except Exception as ex:
    msg = 'Error when querying channel values from GlobalLad'
    logger.error(traceback.format_exc())
    raise Exception(msg) from ex

  # convert data to format required by server spec

  for eha in ehas:
    eha_dict = get_eha_dict(sessionId=int(eha['sessionNumber']),
                channelId=str(eha['channelId']),
                dn=str(eha['dn']),
                eu=(float(eha['eu']) if (eha['eu'] != "") else None),
                vcId=(int(eha['vcid']) if (eha['vcid'] != "") else None),
                channelName=None,
                channelType=str(eha['channelType']),
                channelStatus=str(eha['status']),
                dnAlarmState=str(eha['dnAlarmLevel']),
                euAlarmState=str(eha['euAlarmLevel']),
                sclk=str(eha['sclk']),
                ert=doyToIsoZ(normalize_with_microsecs(eha['ert'])),
                scet=doyToIsoZ(normalize_with_microsecs(eha['scet'])),
                isRecorded=(not str2bool(eha['isRealTime'])))
    eha_dicts.append(eha_dict)

  logger.info(f'Got {len(ehas)} EHA results from GlobalLad.')

  return eha_dicts

