import logging
logger = logging.getLogger(__name__)

from enum import Enum
import csv
import sys
from datetime import datetime, timedelta
import os
import traceback
from datetime import datetime, timezone
import socket
from .config import SCLKSCET_LOOKBACK

import subprocess
from io import StringIO

command_type_mapping = {
  "0": "HW_COMMAND",
  "1": "FSW_COMMAND",
  "2": "BINARY_FILE" 
}

###########################################################
###### MAPPINGS BETWEEN JSON INPUTS AND CHILL INPUTS ######
###########################################################



class VenueType (Enum):
  WSTS = "WSTS"
  TESTBED = "TESTBED"
  ATLO = "ATLO"


def get_utc():
  return datetime.now(tz=timezone.utc)

def get_utc_iso():
  return get_utc().isoformat()

class TimeParsingError (Exception):
  def __init__(self, message):

    # Call the base class constructor with the parameters it needs
    super(TimeParsingError, self).__init__(message)

    # Now for your custom code...
    self.message = message

class ErrorCapturing(list):
  '''
  Context Manager for capturing errors
  '''
  def __enter__(self):
    self._stderr = sys.stderr
    sys.stderr = self._stringio = StringIO()
    return self
  def __exit__(self, *args):
    self.extend(self._stringio.getvalue().splitlines())
    del self._stringio
    sys.stderr = self._stderr

def get_last_error_from_logs (filepath,filters):
  # make sure file exists otherwise raise unique error only capable
  # of being caught by cmd_server
  if (os.path.isfile(filepath)==False):
    raise InvalidFilePathError

  cmd = ['tail', '-n', '50', filepath]
  log_tail = subprocess.check_output(cmd,stderr=subprocess.STDOUT,timeout=30).decode('utf-8')

  error_found = False
  error_list = []
  for line in reversed(log_tail.splitlines()):
    if "ERROR" in line or "FATAL" in line:
      error_found = True
      error_list.append(line)
      break
      
  if error_found is False:
    error_list = ["Error message could not be found in MTAK error logs"]

  return ("\n".join(error_list)).strip()


def update_timeout (start_time,old_timeout):
  '''
  :param start_time: time before a chunk of code was run (datetime object)
  :return: remaining timeout period  (float) , current UTC datetime
  '''
  elapsed_time = (datetime.utcnow() - start_time).total_seconds()
  if (elapsed_time >= old_timeout):
    raise TimeoutError
  else:
    return (old_timeout-elapsed_time,datetime.utcnow())

def normalize_with_microsecs (ftime):
  if '.' in ftime:
    time_segs = ftime.split('.')
    subsecond = str(time_segs[1])
    # If number of digits after decimal point is greater than 6 (e.g., nano precision),
    # truncate to the 6th digit
    if len(subsecond) > 6:
      subsecond = subsecond[0:6]
    return (time_segs[0] + '.' + subsecond)
  else:
    # exact second may not contain subsecond portion
    return ftime + '.000000'

def query_process (cmd, timeout):
  ''' Create a subprocess to send chill queries and return response'''
  # try to send query and return response
  logger.info("Starting subprocess at time: "+datetime.utcnow().isoformat())
  logger.info("Subprocess query command: " + str(cmd))
  resp = subprocess.check_output(cmd,stderr=subprocess.STDOUT,timeout=timeout).decode('utf-8')
  logger.info("Received response at time: "+datetime.utcnow().isoformat())
  if resp:
    # Fix for ING-4207
    # rsyslogd limits to 2048 bytes per message by default.
    # Show only 1024 chars to be conservative.
    if len(resp) > 1024:
      abridged_resp = resp[:512] + '\n ...... \n' + resp[-512:]
      logger.info("QUERY RESPONSE (abridged from %s chars): %s" % (len(resp), abridged_resp))
    else:
      logger.info("QUERY RESPONSE: %s" % resp)
  else:  
    logger.info("QUERY RESPONSE: %s" % resp)
  return resp

def get_csv_row_reader (csv_str):
  rows = csv_str.splitlines()
  reader = csv.reader(rows)
  return reader

def get_hostname():
  '''
  Returns hostname of the current machine
  '''
  return socket.gethostname()

def get_venue_type() -> VenueType:
  '''
  Returns venue type (WSTS, ATLO, or TESTBED) as enums
  '''
  vtype = os.environ.get("INGENIUM_VENUE_TYPE").upper()
  if (vtype=="WSTS" or vtype=="ATLO" or vtype=="TESTBED"):
    return VenueType(vtype)
  elif vtype is None or vtype == "":
    raise VenueTypeNotFound("INGENIUM_VENUE_TYPE environment variable is unassigned.")
  else:
    raise VenueTypeNotFound("Environment variable INGENIUM_VENUE_TYPE=%s. "
                            "Expecting WSTS, ATLO, or TESTBED."%(vtype))

def get_testbed_name():
  '''
  Returns testbed name, either string if it exists or None
  '''
  tb_name = os.environ.get("INGENIUM_TESTBED_NAME")
  if (tb_name is None or tb_name.strip()==""):
    return None
  else:
    return tb_name


def get_sse_hostname():
  '''
  Returns hostname of the venue where sse and vxworks are being run
  '''
  sse_host = os.environ.get("INGENIUM_SSE_HOSTNAME")
  if (sse_host is None or sse_host.strip()==""):
    return None
  else:
    return sse_host

def str_to_datetime (doy_or_iso_str,must_have_Z=False):
  '''

  :param doy_or_iso_str: DOY or ISO formatted string (accepts with or without Z or milliseconds)
  :return: datetime if string matches DOY or ISO. Else raises valueError if not found
  '''
  try:
    return iso_to_datetime(doy_or_iso_str,must_have_Z)
  except ValueError:
    pass
  return doy_to_datetime(doy_or_iso_str)

def iso_to_datetime (doy,must_have_Z=False):
  '''
  :param iso time - can have with or without Zs (string)
  :return: datetime
  '''
  if (doy.endswith('Z')):
    try:
      return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
      pass
    return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%SZ")
  elif (not doy.endswith('Z') and must_have_Z):
    raise ValueError
  else:
    try:
      return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
      pass
    return datetime.strptime(doy, "%Y-%m-%dT%H:%M:%S")

def doy_to_datetime (doy):
  '''
  :param doy (string)
  :return: datetime
  '''
  try:
    return datetime.strptime(doy, "%Y-%jT%H:%M:%S.%f")
  except ValueError:
    pass

  return datetime.strptime(doy, "%Y-%jT%H:%M:%S")

def datetime_to_doy (dt,res=None):
  if res == None:
    dtstr = datetime.strftime(dt,'%Y-%jT%H:%M:%S')
  elif res == 'millis':
    dtstr = datetime.strftime(dt, '%Y-%jT%H:%M:%S.%f')
    dtstr = dtstr[:-3]
  elif res == 'micros':
    dtstr = datetime.strftime(dt, '%Y-%jT%H:%M:%S.%f')
  return dtstr

def datetime_to_isoZ (dt,res=None):
  if res == None:
    dtstr = datetime.strftime(dt,'%Y-%m-%dT%H:%M:%S')
  elif res == 'millis':
    dtstr = datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%f')
    dtstr = dtstr[:-3]
  elif res == 'micros':
    dtstr = datetime.strftime(dt, '%Y-%m-%dT%H:%M:%S.%f')
  return dtstr

def utc_now_doy():
  utc_now = datetime.utcnow()
  utc_doy = datetime.strftime(utc_now, "%Y-%jT%H:%M:%S.%f")
  return utc_doy

def doyToIsoZ (doy):
  '''
  doy time in string
  '''
  dt = datetime.strptime(doy, "%Y-%jT%H:%M:%S.%f")
  down_to_micro_sec = datetime.strftime(dt,'%Y-%m-%dT%H:%M:%S.%f')
  down_to_milli_sec = down_to_micro_sec[:-3]
  return down_to_milli_sec + 'Z'

def get_msg_with_traceback(details):
  err_msg = "Error: " + details + "\nTRACEBACK:" + traceback.format_exc()
  return err_msg

def get_now_isoZ():
  return normalize_with_microsecs(datetime.utcnow().isoformat())[:-3] + 'Z'

def get_sclkscet_times():

  # remember to format as DOY

  # end time: now
  end_time_utc = datetime.utcnow()
  end_time = datetime.strftime(end_time_utc, '%Y-%jT%H:%M:%S')

  # start time: 30 seconds ago
  start_time_utc = datetime.utcnow() - timedelta(seconds=SCLKSCET_LOOKBACK)
  start_time = datetime.strftime(start_time_utc, '%Y-%jT%H:%M:%S')

  # return both start and end times
  return start_time, end_time

def most_recent_datetime(query_response):

  latest_datetime = None

  for res in query_response:

    if latest_datetime is None:
      latest_datetime = res
    elif res["sclk"] > latest_datetime["sclk"]:
      latest_datetime = res
    else:
      pass

  return latest_datetime

def return_validated_start_end_times(start_time, end_time, time_type, duration):

  if start_time is not None:
    try:
      validated_start_time_type, start_time = validate_time(start_time)
    except TimeParsingError:
      raise TimeParsingError("Start time is in an invalid format: %s"% start_time)
  if end_time is not None:
    try:
      validated_end_time_type, end_time = validate_time(end_time)
    except TimeParsingError:
      raise TimeParsingError("End time is in an invalid format: %s"% end_time)
  if duration is not None:
    if start_time is not None and end_time is not None:
      raise TimeParsingError("Cannot have both a start time and end time with a duration.")
    if start_time is not None:
      if time_type == "SCET":
        end_time = start_time + timedelta(seconds=duration)
      else:
        end_time = start_time + duration
    
    if end_time is not None:
      if time_type == "SCET":
        start_time = end_time - timedelta(seconds=duration)
      else:
        start_time = end_time - duration

    if end_time < start_time:
      raise TimeParsingError("End time is earlier than start time.")

  return start_time, end_time

def validate_time(input_time):
  """
  This function will attempt to parse the provided time and will return either a datetime object if
  successful (depending on format).
  """

  parsing=True
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%jT%H:%M:%S.%f")
      time_type = "SCET"
      parsing=False
    except:
      pass
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%jT%H:%M:%S")
      time_type = "SCET"
      parsing = False
    except:
      pass
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%m-%dT%H:%M:%S")
      time_type = "SCET"
      parsing=False
    except:
      pass
  if parsing:
    try:
      converted_time=datetime.strptime(input_time,"%Y-%m-%dT%H:%M:%S.%f")
      time_type = "SCET"
      parsing=False
    except:
      pass
  if parsing:
    try:
      converted_time=float(input_time)
      time_type = "SCLK"
      parsing=False
    except:
      pass
  if parsing:
    try:
      if "-" in input_time:
        split_time = input_time.split("-")
        if len(split_time) != 2:
          pass
        else:
          for item in split_time:
            int(item)
          time_type = "SCLK"
          parsing=False
      else:
        pass
    except:
      pass
  if parsing:
    raise TimeParsingError("Time parsing error")
  return time_type, converted_time

def str2bool (item):
  if (type(item) == bool):
    return item
  elif type(item) == str:
    return (True if item.lower() == 'true' else False)

def get_env (env_var,cast_type=str):
  val = os.environ.get(env_var)
  if (val is not None and val.strip() != ''):
    if (cast_type == str):
      return str(val)
    elif (cast_type == int):
      return int(val)
  return None

class TimeoutError(Exception):
  pass

class InvalidFilePathError(Exception):
  pass

class ConsolePortFileNotFound (Exception):
  pass

class VenueTypeNotFound (Exception):
  pass

class SocketConnectionError (Exception):
  pass

class TimeParsingError (Exception):
  def __init__(self, message):

    # Call the base class constructor with the parameters it needs
    super(TimeParsingError, self).__init__(message)

    # Now for your custom code...
    self.message = message


