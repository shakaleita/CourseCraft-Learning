import importlib,os,sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
temp = tempfile.mkdtemp(prefix='portfolio-test-')
os.environ['APP_DB']=str(Path(temp)/'test.db')
os.environ['OWNER_SETUP_TOKEN']='test-only-setup-token-1234567890123'
if 'main' in sys.modules: del sys.modules['main']
from main import app
client=TestClient(app)
assert client.post('/api/auth/register',json={'username':'qaowner','password':'DemoPassword123!','setup_token':'test-only-setup-token-1234567890123'}).status_code==201
assert client.post('/api/auth/login',json={'username':'qaowner','password':'DemoPassword123!'}).status_code==200

def test_health():
    r=client.get('/api/health')
    assert r.status_code==200 and r.json()['ok']

def test_initial_list():
    r=client.get('/api/items')
    assert r.status_code==200 and isinstance(r.json(),list)

def test_summary():
    r=client.get('/api/summary')
    assert r.status_code==200 and isinstance(r.json(),list)


# v0.3 regression tests
def test_course_completion_and_unenrol():
    course=client.post('/api/items',json={'title':'QA course','instructor':'Example Tutor','lessons':2})
    assert course.status_code==201
    cid=course.json()['id']
    e=client.post('/api/enrol',json={'course_id':cid,'student':'Demo Student'})
    assert e.status_code==200
    eid=e.json()['id']
    assert client.post('/api/enrol',json={'course_id':cid,'student':'Demo Student'}).status_code==409
    for _ in range(4):
        assert client.patch(f'/api/enrolments/{eid}').status_code==200
    report=client.get(f'/api/courses/{cid}/report').json()
    assert report['enrolled']==1 and report['finished']==1 and report['average_progress']==100.0
    assert client.delete(f'/api/enrolments/{eid}').status_code==204
    assert client.get(f'/api/courses/{cid}/report').json()['enrolled']==0



def test_v05_course_completion():
    course=client.post('/api/items',json={'title':'Engineering Basics','instructor':'Demo Instructor','lessons':2}).json()
    enrol=client.post('/api/enrol',json={'course_id':course['id'],'student':'Example Student'}).json()
    assert client.get(f"/api/enrolments/{enrol['id']}/completion").json()['finished'] is False
    client.patch(f"/api/enrolments/{enrol['id']}")
    client.patch(f"/api/enrolments/{enrol['id']}")
    outcome=client.get(f"/api/enrolments/{enrol['id']}/completion").json()
    assert outcome['finished'] and outcome['demo_certificate_id']

def test_v05_authentication():
    with TestClient(app) as anonymous:
        assert anonymous.get('/api/items').status_code==401
        assert anonymous.post('/api/auth/register',json={'username':'intruder','password':'DemoPassword123!','setup_token':'bad'}).status_code==403

# v0.6 request-origin and owner audit regression
def test_v06_audit_record_and_cross_site_guard():
    attempted=client.post('/api/__audit_probe_404')
    assert attempted.status_code==404
    audit=client.get('/api/auth/audit')
    assert audit.status_code==200
    assert any(row['method']=='POST' and row['path']=='/api/__audit_probe_404'
               and row['status_code']==404 for row in audit.json())
    assert client.get('/api/auth/audit',params={'limit':201}).status_code==422
    blocked=client.post('/api/__audit_probe_404',headers={'sec-fetch-site':'cross-site'})
    assert blocked.status_code==403
