import importlib,os,sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
temp = tempfile.mkdtemp(prefix='portfolio-test-')
os.environ['APP_DB']=str(Path(temp)/'test.db')
if 'main' in sys.modules: del sys.modules['main']
from main import app
client=TestClient(app)

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

