# Disposable SQLite startup and erase security metadata verification; no live database access.
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import server
from db import get_conn, init_db, one, rows
from company import erase_records, EraseIn
import os
server.startup()
with get_conn() as c:
    account=one(c,'SELECT * FROM users LIMIT 1')
    assert one(c,'SELECT COUNT(*) n FROM categories')['n']>0
    c.execute("INSERT INTO session_revocations VALUES ('TEST_security',9999999999)")
    c.execute("INSERT INTO login_attempts VALUES ('TEST_security','TEST_user',5,9999999999)")
before=None
with get_conn() as c:before={t:rows(c,'SELECT * FROM '+t) for t in ['users','categories','drivers','trucks','telemetry_sources','company_settings','session_revocations','login_attempts']}
assert erase_records(EraseIn(confirmation='ERASE ALL RECORDS',owner_password=os.environ['OWNER_PASSWORD']),account)['ok']
init_db();server.startup()
with get_conn() as c:
    assert {t:rows(c,'SELECT * FROM '+t) for t in before}==before
with get_conn() as c:c.execute('DELETE FROM categories')
init_db();server.startup()
with get_conn() as c:assert rows(c,'SELECT * FROM categories')==[]
print('PASS erase preserves setup and security metadata; individually deleted categories remain empty after restart')