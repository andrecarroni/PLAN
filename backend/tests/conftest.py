import os
os.environ['DATABASE_URL']=os.getenv('TEST_DATABASE_URL','sqlite:////tmp/p4_rebuild_test.db')
os.environ['APP_ENV']='test'
from sqlalchemy.engine import make_url
if 'test' not in (make_url(os.environ['DATABASE_URL']).database or '').lower():raise RuntimeError('Use um banco exclusivo de testes cujo nome contenha test.')
import pytest
from sqlalchemy import select,text
from fastapi.testclient import TestClient
from app.db import Base,engine,SessionLocal
from app.main import app
from app.models import User
from app.security import hash_password,now,annual
PASSWORD='SenhaFicticia-12345'
@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for i,roles in enumerate([['aluno'],['aluno'],['consultor'],['vendedor'],['administrador'],['consultor','vendedor'],['aluno','consultor']],start=1):
            db.add(User(id=i,name=f'Pessoa fictícia {i}',phone=f'+55119999900{i:02d}',password_hash=hash_password(PASSWORD),roles=roles,status='ativo',released_at=now(),expires_at=annual(now())))
        db.commit()
        if engine.dialect.name=='postgresql':db.execute(text("SELECT setval(pg_get_serial_sequence('users','id'),(SELECT max(id) FROM users))"));db.commit()
    yield
@pytest.fixture
def login():
    clients=[]
    def factory(uid=1):
        c=TestClient(app);clients.append(c);r=c.post('/api/auth/login',json={'phone':f'+55119999900{uid:02d}','password':PASSWORD});assert r.status_code==200,r.text;c.headers['X-CSRF-Token']=r.json()['csrf'];return c
    yield factory
    for c in clients:c.close()
@pytest.fixture
def payload():
    def factory(c,sid=1):
        p=c.get(f'/api/plans/{sid}').json();p.pop('id');p.pop('user_id');p['start']='2026-11';p['selected_month']='2026-11';return p
    return factory

def entry(category='rendas',value='1000.00',month='2026-11',**kw):
    return {'key':category,'category':category,'label':category,'month':month,'forecast':value,'actual':None,'deducted':False,'method':'outro','absent':False,**kw}
