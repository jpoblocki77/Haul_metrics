# Executes real bridge entrypoints with simulated stdlib network/input, never product API mocks.
import builtins, getpass, io, json, os, runpy, sys
from urllib.error import HTTPError, URLError
import urllib.request
import time

path, mode = sys.argv[1:]
inputs = iter([os.environ['REACT_APP_BACKEND_URL'], 'TEST_username', '', '']) if mode == 'source' else iter(['TEST_username', 'TEST_username', '', ''])
def prompt(message):
    print('PROMPT '+message, flush=True)
    return next(inputs, '')
builtins.input = prompt
getpass.getpass = lambda message: 'TEST_secret_password'
count = 0
class Reply:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,*args): return json.dumps(self.data).encode()
def network(req, **kwargs):
    global count
    url=req.full_url
    print('REQUEST '+url, flush=True)
    if url.endswith('/auth/login'):
        count+=1
        if mode == 'network': raise URLError('TEST_private_remote_error')
        if mode == 'retry' and count == 1: raise HTTPError(url,401,'TEST_private',{},io.BytesIO())
        if mode == 'lockout': raise HTTPError(url,429,'TEST_private',{},io.BytesIO())
        return Reply({'token':'TEST_secret_token'})
    if url.endswith('/telemetry/status'):
        if mode == 'expired': raise HTTPError(url,401,'TEST_private',{},io.BytesIO())
        return Reply({'source':{'enabled':True,'server_url':'http://127.0.0.1:25555/api/ets2/telemetry'}})
    if '127.0.0.1' in url:
        if mode == 'scs': raise URLError('TEST_private_remote_error')
        return Reply({'game':{'connected':True},'truck':{}})
    return Reply({'accepted':True})
urllib.request.urlopen=network
def stop(seconds):
    print('SLEEP '+str(seconds),flush=True)
    raise KeyboardInterrupt()
time.sleep=stop
runpy.run_path(path,run_name='__main__')