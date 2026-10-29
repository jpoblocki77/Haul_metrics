# Worker restart contracts use disposable SQLite storage, never the live company database.
import os, subprocess, sys
from pathlib import Path

def test_security_and_telemetry_survive_worker_restart(tmp_path):
    env={**os.environ,'SQLITE_DB_FILE':str(tmp_path/'isolated.db')}
    worker=Path(__file__).with_name('isolated_persistence_worker.py')
    for phase in ['write','read']:
        result=subprocess.run([sys.executable,str(worker),phase,str(tmp_path/'tokens.json')],env=env,capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stdout+result.stderr
        print(result.stdout)