import logging
import sys
from starlette.concurrency import iterate_in_threadpool

def restore_root_logger():
    # restore root logger that was crippled by MTAK
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    for handler in root_logger.handlers:
        handler.setLevel(logging.DEBUG)

def listloggers():
    rootlogger = logging.getLogger()
    print(rootlogger)
    for h in rootlogger.handlers:
        print('     %s' % h)

    for nm, lgr in logging.Logger.manager.loggerDict.items():
        if isinstance(lgr, logging.PlaceHolder):
            print('+ [%-20s] %s' % (nm, lgr))
        else:
            print('+ [%-20s] %s propagate: %s' % (nm, lgr, lgr.propagate))
            for h in lgr.handlers:
                print('     %s' % h)

# import this first since MTAK messes up logging of other modules
from core import venue_core
restore_root_logger()

import os

logger = logging.getLogger(__name__)

def print_env_variables():
    logger.info('ENVIRONMENT VARIABLES:')
    names = [
        'ING_VENUE_DIR',
        'ING_MTAK_DIR',
        'ING_LOG_DIR',
        'LAD_HOST',
        'LAD_PORT',
        'LAD_HTTPS',
        'PATH',
        'GDS_JAVA_OPTS'
    ]
    for name in names:
        value = os.environ.get(name)
        logger.info(f'{name}: {value}')

    for index, path in enumerate(sys.path):
        logger.info(f'sys.path {index+1}: {path}')

print_env_variables()

import traceback
import sys
import argparse
import io
import random
import string
import time
import math
import yaml
import json
import pyaml_env
import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
# from core import core_util
from core.schema import MtakStartBodyModel, FswCmdBodyModel, HwCmdBodyModel, \
    SseCmdBodyModel, BinaryFileBodyModel, ScmfFileBodyModel, \
    HealthStatus, HealthStatusEnum, \
    MtakStartResponse, ErrorResponse, \
    CmdDispatchedResp
from fastapi.exceptions import RequestValidationError
import utils

utils.print_key_info()

LOG_CONFIG_YAML = 'log_config.yaml'

prefix_router = APIRouter(prefix='/api/v3')


def check_default_cmd_string(default_cmd_string):
  # if string_id is value 'default' set string_id to None. Else, proceed with input string id
  if default_cmd_string in ['A', 'B', 'AB']:
    return default_cmd_string
  else:
    return None


@prefix_router.get('/health', 
                    responses={
                        200: {'model': HealthStatus},
                        400: {'model': ErrorResponse}
                    },
                    summary='Check health status of VenueServer',
                    tags=['HEALTH']
                )
def health() -> HealthStatus:
    # listloggers()
    return HealthStatus(status=HealthStatusEnum.OK.value, message='')


@prefix_router.post('/mtak/start',
                    responses={
                        200: {'model': MtakStartResponse},
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Start MTAK on the venue GDS host for the specified AMPCS session ids',
                    tags=['MTAK']
                )
def start_mtak(body: MtakStartBodyModel, response: Response):
    try:
        logger.info('calling core_start_mtak')

        logger.info(f'defaultCmdString: {body.defaultCmdString.value} {type(body.defaultCmdString.value)}')

        sessionIds, startTime = venue_core.core_start_mtak(sessionIds=body.sessionIds,
                                   defaultCmdString=body.defaultCmdString.value,
                                   timeout=body.timeout)

        return MtakStartResponse(sessionIds=sessionIds, startTime=startTime)
    except Exception as ex:
        msg = 'Unexpected error in /mtak/start'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')


@prefix_router.post('/mtak/shutdown', 
                    status_code=204,
                    responses={
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Shutdown MTAK that was started by VenueServer',
                    tags=['MTAK']
                )
def shutdown_mtak(response: Response):
    try:
        venue_core.core_stop_mtak()
        return Response(status_code=204)
    except Exception as ex:
        msg = 'Unexpected error in /mtak/shutdown'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')


@prefix_router.post('/cmd/fsw_cmd',
                    responses={
                        200: {'model': CmdDispatchedResp},
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Send a FSW command via MTAK',
                    tags=['COMMAND']
                )
def fsw_cmd(body: FswCmdBodyModel, response: Response):
    try:
        string_selection = check_default_cmd_string(body.stringSelection.value)

        cmdRequested, dispatchTime = venue_core.core_send_fsw_cmd(sessionId=body.sessionId,
                                    validate=body.validate_,
                                    cmdString=body.commandString,
                                    stringSelection=string_selection,
                                    timeout=body.timeout)
        
        return JSONResponse(status_code=200, content={'cmdRequested': cmdRequested, 'dispatchTime': dispatchTime})
    except Exception as ex:
        msg = 'Failed to send FSW command'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')


@prefix_router.post('/cmd/hw_cmd',
                    responses={
                        200: {'model': CmdDispatchedResp},
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Send a HW command via MTAK',
                    tags=['COMMAND']
                )
def hw_cmd(body: HwCmdBodyModel, response: Response):
    try:
        string_selection = check_default_cmd_string(body.stringSelection.value)

        cmdRequested, dispatchTime = venue_core.core_send_hw_cmd(sessionId=body.sessionId,
                                    cmdStem=body.commandStem,
                                    stringSelection=string_selection,
                                    timeout=body.timeout)
        return JSONResponse(status_code=200, content={'cmdRequested': cmdRequested, 'dispatchTime': dispatchTime})
    except Exception as ex:
        msg = 'Failed to send HW command'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')

@prefix_router.post('/cmd/sse',
                    responses={
                        200: {'model': CmdDispatchedResp},
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Send a SSE command via MTAK',
                    description='Send a SSE (Simulation and Support Equipment) command via MTAK',
                    tags=['COMMAND']
                )
def sse_cmd(body: SseCmdBodyModel, response: Response):
    try:
        cmdRequested, dispatchTime = venue_core.core_send_sse_cmd(sessionId=body.sessionId,
                                    cmdString=body.commandString,
                                    timeout=body.timeout)
        return JSONResponse(status_code=200, content={'cmdRequested': cmdRequested, 'dispatchTime': dispatchTime})
    except Exception as ex:
        msg = 'Failed to send SSE command'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')


@prefix_router.post('/cmd/binary_file',
                    responses={
                        200: {'model': CmdDispatchedResp},
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Upload a file to flight computer via MTAK',
                    tags=['COMMAND']
                )
def binary_file(body: BinaryFileBodyModel, response: Response):
    try:
        string_selection = check_default_cmd_string(body.stringSelection.value)
        
        cmdRequested, dispatchTime = venue_core.core_send_fsw_file(
            sessionId=body.sessionId,                                                
            sourcePath=body.sourceFilePath,
            targetLoc=body.targetFilePath,
            fileType=body.fileType,
            overwrite=body.overwrite,
            stringSelection=string_selection,
            timeout=body.timeout)
        return JSONResponse(status_code=200, content={'cmdRequested': cmdRequested, 'dispatchTime': dispatchTime})
    except Exception as ex:
        msg = f'Failed to send a file: {body.sourceFilePath}'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')

    
@prefix_router.post('/cmd/scmf',
                    responses={
                        200: {'model': CmdDispatchedResp},
                        400: {'model': ErrorResponse},
                        401: {'model': ErrorResponse},
                        403: {'model': ErrorResponse}
                    },
                    summary='Upload a SCMF file to flight',
                    tags=['COMMAND']    
                )
def scmf_file(body: ScmfFileBodyModel, response: Response):
    try:        
        cmdRequested, dispatchTime = venue_core.core_send_scmf_file(
            sessionId=body.sessionId,                                                
            filePath=body.filePath,
            disableChecks=body.disableChecks,
            timeout=body.timeout)
        return JSONResponse(status_code=200, content={'cmdRequested': cmdRequested, 'dispatchTime': dispatchTime})
    except Exception as ex:
        msg = f'Failed to send a SCMF file: {body.filePath}'
        logging.exception(msg)
        response.status_code = 400
        return ErrorResponse(message=f'{msg}. {traceback.format_exc()}')


# router needs to be added after end point definitions
app = FastAPI()
app.include_router(prefix_router)


@app.middleware('http')
async def check_jwt(request: Request, call_next):
    request.state.username = ''

    if request.url.path == '/docs':
        # docs end point does not require JWT token
        return await call_next(request)    
    if request.url.path == '/openapi.json':
        # docs end point does not require JWT token
        return await call_next(request)
    if request.url.path == '/openapi.yaml':
        # docs end point does not require JWT token
        return await call_next(request)
    
    if request.url.path.endswith('/health'):
        # health end point does not require JWT token
        return await call_next(request)
    else:
        authorization_header = request.headers.get('Authorization')
        try:
            jwt_decoded = utils.get_decoded_token(authorization_header)
            # cache username info for this request
            # See: https://fastapi.tiangolo.com/tutorial/sql-databases/#about-requeststate
            request.state.username = jwt_decoded.get('username', '')
        except Exception:
            return JSONResponse(status_code=401, 
                content={'message': f'Invalid API token. {traceback.format_exc()}'})

        if utils.has_permission(jwt_decoded):
            return await call_next(request)
        else:
            return JSONResponse(status_code=403, 
                content={
                    'message': f'Does not have the required permission. Need one of {utils.ACCEPTED_SCOPES}'
                })

@app.middleware('http')
async def log_request(request: Request, call_next):
    request_id = ''.join(random.choices(string.ascii_uppercase, k=6))
    logger.info(f'{request_id}: {request.method} {request.url.path}')
    start_time = time.time()
    
    response = await call_next(request)
    
    elapsed_msec = (time.time() - start_time) * 1000
    # username is available after the request has been processed
    username = request.state.username if hasattr(request.state, 'username') else ''

    # response is "StreamingResponse" class. We need to the response content as a string to log.
    # See https://stackoverflow.com/questions/71882419/fastapi-how-to-get-the-response-body-in-middleware
    content_type = response.headers.get('content-type')
    response_content = ''
    if content_type and content_type.lower() == 'application/json':
        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        response_content = b''.join(response_body).decode()

    log_max_chars = 1000
    if response.status_code >= 200 and response.status_code < 400:
        if len(response_content) > log_max_chars:
            logger.info(f'{request_id}: completed in {elapsed_msec:.2f} msec.' + 
                        f' status_code: {response.status_code} username: {username} response_content (total_length: {len(response_content)}): {response_content[:log_max_chars]}')
        else:
            logger.info(f'{request_id}: completed in {elapsed_msec:.2f} msec.' + 
                        f' status_code: {response.status_code} username: {username} response_content: {response_content}')
    else:
        logger.warning(f'{request_id}: completed in {elapsed_msec:.2f} msec.' + 
                    f' status_code: {response.status_code} username: {username} response_content: {response_content}')
    
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    error_json_str = json.dumps(exc.json(indent=None))
    return JSONResponse(status_code=400, 
        content={'message': str(exc)})


### OPENAPI ###

tags_metadata = [
    {
        'name': 'MTAK',
        'description': 'Start or stop MTAK sessions'
    },
    {
        'name': 'COMMAND',
        'description': 'Send commands'
    },
    {
        'name': 'HEALTH',
        'description': 'Check service health'
    }
]

@app.get('/openapi.yaml', include_in_schema=False)
def openapi_yaml() -> Response:
    # Convert API specs in JSON to YAML.
    # See https://github.com/tiangolo/fastapi/issues/1140
    specs_json= app.openapi()
    yaml_str_io = io.StringIO()
    yaml.dump(specs_json, yaml_str_io)
    return Response(yaml_str_io.getvalue(), media_type='text/yaml')

def custom_openapi():
    try:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title='Ingenium VenueServer',
            version='14.1-TP',
            description='RESTful API of Ingenium VenueServer that interfaces with test venues',
            routes=app.routes,
            tags=tags_metadata
        )

        for _, method_item in openapi_schema.get('paths').items():
            for _, param in method_item.items():
                responses = param.get('responses')
                # remove the default 422 response fro OpenAPI, which was overriden as 400 response
                if '422' in responses:
                    del responses['422']
        # cache the schema
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    except:
        logger.error(traceback.format_exc())

# override openapi method
app.openapi = custom_openapi

def parse_args():
    parser = argparse.ArgumentParser(description='Ingenium VenueServer', 
        prog='main.py',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', '-p', type=int, default=19443,
                        help='port number of the service')
    return parser.parse_args()

if __name__ == '__main__':
    log_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), LOG_CONFIG_YAML))
    if os.path.isfile(log_config_path):
        logger.info(f'Load log configuration from: {log_config_path}')
    else:
        logger.error(f'Log configuration file does not exist. Exit. {log_config_path}')
        sys.exit(1)
    try:
        log_config = pyaml_env.parse_config(log_config_path)
    except Exception as ex:
        logger.exception(f'Failed to load log configuration file: {log_config_path}')
        sys.exit(1)

    args = parse_args()
    
    uvicorn.run('main:app', host='127.0.0.1', port=args.port, reload=False, log_config=log_config, workers=1)
