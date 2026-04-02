# import mtak first since this messes up logging
from .mtak_cmd import mtak_startup_timeout, mtak_shutdown, \
  mtak_send_fsw_cmd, mtak_send_hw_cmd, mtak_send_sse_cmd, \
  mtak_send_fsw_file, mtak_send_scmf_file

import logging
logger = logging.getLogger(__name__)

from .core_utils import get_now_isoZ

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

