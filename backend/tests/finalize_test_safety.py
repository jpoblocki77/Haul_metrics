# Remove only disposable test lockouts and restrict encrypted safety archives; never alter real accounts.
import json,sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parents[1]/'.env')
sys.path.insert(0,str(Path(__file__).parents[1]))
from db import get_conn,rows
with get_conn() as conn:
    users=rows(conn,'SELECT username FROM users')
    assert {u['username'] for u in users}=={'owner','dispatch1'}
    attempts=rows(conn,"SELECT identifier FROM login_attempts WHERE username GLOB 'test_r4_*'")
    conn.execute("DELETE FROM login_attempts WHERE username GLOB 'test_r4_*'")
for file in Path('/app/test_reports').rglob('*.mccoy'):file.chmod(0o600)
result={'removed_only_test_lockouts':len(attempts),'real_accounts_unchanged':True,'encrypted_safety_archives_permissions':'0600'}
Path('/app/test_reports/final_test_safety.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))