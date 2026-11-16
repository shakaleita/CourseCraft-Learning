APP_TITLE = 'CourseCraft'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import sqlite3, os
from contextlib import contextmanager
from pathlib import Path

DB = Path(os.environ.get("APP_DB", str(Path(__file__).parent / "app.db")))
app = FastAPI(title=APP_TITLE, version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"])

@contextmanager
def db():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def rows(cursor):
    return [dict(r) for r in cursor.fetchall()]

def setup(sql):
    with db() as con:
        con.executescript(sql)

@app.get("/api/health")
def health():
    return {"ok": True, "service": APP_TITLE}


setup("""CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,title TEXT NOT NULL,instructor TEXT NOT NULL,category TEXT NOT NULL DEFAULT 'General',lessons INTEGER NOT NULL CHECK(lessons>0));CREATE TABLE IF NOT EXISTS enrolments(id INTEGER PRIMARY KEY,course_id INTEGER NOT NULL,student TEXT NOT NULL,completed INTEGER NOT NULL DEFAULT 0,UNIQUE(course_id,student),FOREIGN KEY(course_id) REFERENCES courses(id));""")
class Course(BaseModel):
    title:str
    instructor:str
    category:str="General"
    lessons:int=8
class Enrol(BaseModel):
    course_id:int
    student:str
@app.get('/api/items')
def items():
    with db() as c:return rows(c.execute('SELECT * FROM courses ORDER BY id DESC'))
@app.post('/api/items',status_code=201)
def create_item(d:Course):
    if not d.title.strip() or d.lessons<=0:raise HTTPException(422,'Invalid course')
    with db() as c:
        cur=c.execute('INSERT INTO courses(title,instructor,category,lessons) VALUES(?,?,?,?)',(d.title,d.instructor,d.category,d.lessons))
        return dict(c.execute('SELECT * FROM courses WHERE id=?',(cur.lastrowid,)).fetchone())
@app.post('/api/enrol')
def enrol(d:Enrol):
    try:
        with db() as c:
            cur=c.execute('INSERT INTO enrolments(course_id,student) VALUES(?,?)',(d.course_id,d.student))
            return {'id':cur.lastrowid,'completed':0}
    except sqlite3.IntegrityError:raise HTTPException(409,'Already enrolled or invalid course')
@app.get('/api/enrolments')
def enrolments():
    with db() as c:return rows(c.execute('SELECT e.*,c.title,c.lessons FROM enrolments e JOIN courses c ON c.id=e.course_id'))
@app.patch('/api/enrolments/{id}')
def progress(id:int):
    with db() as c:
        cur=c.execute('UPDATE enrolments SET completed=MIN(completed+1,(SELECT lessons FROM courses WHERE id=course_id)) WHERE id=?',(id,))
        if not cur.rowcount:raise HTTPException(404,'Enrolment not found')
        return dict(c.execute('SELECT * FROM enrolments WHERE id=?',(id,)).fetchone())
@app.get('/api/summary')
def summary():
    with db() as c:return [{'label':'Courses','value':c.execute('SELECT COUNT(*) FROM courses').fetchone()[0]},{'label':'Enrolments','value':c.execute('SELECT COUNT(*) FROM enrolments').fetchone()[0]}]


# v0.3: course completion reporting
@app.get('/api/courses/{course_id}/report')
def course_report(course_id: int):
    with db() as con:
        course=con.execute('SELECT * FROM courses WHERE id=?',(course_id,)).fetchone()
        if not course:
            raise HTTPException(404,'Course not found')
        data=con.execute("""SELECT COUNT(*) AS enrolled,
            COALESCE(SUM(CASE WHEN completed>=? THEN 1 ELSE 0 END),0) AS finished,
            COALESCE(ROUND(AVG(100.0*completed / ?),1),0) AS average_progress
            FROM enrolments WHERE course_id=?""",(course['lessons'],course['lessons'],course_id)).fetchone()
        return {'course':dict(course),**dict(data)}

@app.delete('/api/enrolments/{enrolment_id}',status_code=204)
def unenrol(enrolment_id: int):
    with db() as con:
        if not con.execute('DELETE FROM enrolments WHERE id=?',(enrolment_id,)).rowcount:
            raise HTTPException(404,'Enrolment not found')


import hashlib
@app.get('/api/enrolments/{enrolment_id}/completion')
def completion(enrolment_id:int):
    with db() as con:
        record=con.execute("""SELECT e.id,e.student,e.completed,c.id AS course_id,c.title,c.lessons
            FROM enrolments e JOIN courses c ON c.id=e.course_id WHERE e.id=?""",(enrolment_id,)).fetchone()
        if not record:raise HTTPException(404,'Enrolment not found')
        info=dict(record)
        info['progress_percent']=round(info['completed']*100/info['lessons'],1)
        info['finished']=info['completed']>=info['lessons']
        info['demo_certificate_id']=(hashlib.sha256(f"{info['id']}:{info['course_id']}:{info['student']}".encode()).hexdigest()[:16]
             if info['finished'] else None)
        return info

from security import install_auth
install_auth(app,DB)
