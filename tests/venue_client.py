import requests
import sys
import os
import time
import jwt
import socket

PRIVATE_PEM_FILE = 'exec_venue_private_pem.pem'

server_1 = 'http://localhost:19443/api/v3'
server_2 = 'http://localhost:19444/api/v3'

session_id_a = int(os.environ.get('TEST_AMPCS_SESSION_ID_A', 0))
session_id_b = int(os.environ.get('TEST_AMPCS_SESSION_ID_B', 0))

private_pem_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 
                               PRIVATE_PEM_FILE)
exec_venue_private_pem_file = open(private_pem_path, 'r')
exec_venue_private_pem = exec_venue_private_pem_file.read()

username = os.environ.get('USER', '')

exec_shared_dict = {}

def generate_exec_token():
    iat = int(time.time()) - 60
    exp = iat + (30*60)
    exec_headers = {'Content-Type': 'application/json',
              'Accept': 'application/json'}
    encoded_token = jwt.encode({'scopes': ['basic', 'execute:wsts', 'execute:testbed', 'execute:sit', 'execute:other', 'redline', 'config_mgmt', 'admin'],
                        'exp':exp,
                        'iat':iat,
                        'username': username},
                         exec_venue_private_pem,
                         algorithm='RS256')

    token_str = encoded_token if isinstance(encoded_token, str) else encoded_token.decode('utf-8')
    auth_header = 'Bearer {0}'.format(token_str)
    exec_headers['Authorization'] = auth_header
    exec_shared_dict['headers'] = exec_headers  

generate_exec_token()

###
hostname = socket.gethostname()
if hostname.startswith('eurc'):
    CMD_NO_OP = 'CMD_NO_OP'

elif hostname.startswith('psyche'):
    CMD_NO_OP = 'CMD_NO_OP'
else:
    print(f'Error: Unrecognized hostname: {hostname}')
    sys.exit(1)


def start_mtak(server, sessionIds, timeout=60, defaultCmdString='AB'):
    url = f'{server}/mtak/start'
    res = requests.post(url, 
	    json={'sessionIds': sessionIds, 'timeout': timeout, 'defaultCmdString': defaultCmdString},
        headers=exec_shared_dict['headers']
    )
    return res

def shutdown_mtak(server):
    url = f'{server}/mtak/shutdown'
    res = requests.post(url, headers=exec_shared_dict['headers'])
    return res

def send_fsw_cmd(server, sessionId, commandString, validate=False, stringSelection='DEFAULT', timeout=10):
    print(f'commandString: {commandString}')
    url = f'{server}/cmd/fsw_cmd'
    res = requests.post(url, json={
            'sessionId': sessionId, 
            'commandString': commandString, 
            'validate': validate,
            'stringSelection': stringSelection,
            'timeout': timeout
    	},
        headers=exec_shared_dict['headers']
    )
    return res

def send_sse_cmd(server, sessionId, commandString, timeout=10):
    url = f'{server}/cmd/sse'
    res = requests.post(url, json={
            'sessionId': sessionId,
            'commandString': commandString,
            'timeout': timeout
        },
        headers=exec_shared_dict['headers']
    )
    return res

def send_file(server, sessionId, sourceFilePath, targetFilePath, overwrite=True, fileType=0, stringSelection='DEFAULT', timeout=10):
    url = f'{server}/cmd/binary_file'
    res = requests.post(url, json={
            'sessionId': sessionId,
            'sourceFilePath': sourceFilePath,
            'targetFilePath': targetFilePath,
            'overwrite': True,
            'fileType': 0,
            'stringSelection': 'DEFAULT',
            'timeout': 60
        },
        headers=exec_shared_dict['headers']
    )
    return res


def send_scmf_file(server, sessionId, filePath, disableChecks=False, timeout=10):
    url = f'{server}/cmd/scmf'
    res = requests.post(url, json={
            'sessionId': sessionId,
            'filePath': filePath,
            'disableChecks': disableChecks,
            'timeout': 60
        },
        headers=exec_shared_dict['headers']
    )
    return res
