"""Foreground serial command wrapper, restoring every SQLite row even after test failures."""
import os
import subprocess
import sys
from dotenv import dotenv_values
from regression_safety import safeguard

for file in ['/app/backend/.env','/app/frontend/.env']:
    for key,value in dotenv_values(file).items():
        if value is not None:
            os.environ.setdefault(key,value)
with safeguard('outer foreground command'):
    result = subprocess.run(sys.argv[1:], check=False)
sys.exit(result.returncode)