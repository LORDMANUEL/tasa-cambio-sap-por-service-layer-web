from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.auth import create_auth_router
from app.web_auth import password_hash


class Settings:
    web_admin_user='admin'
    web_admin_password_hash=password_hash('admin123')
    web_session_secret='x'*48


def test_auth_router_login_and_logout_contract():
    app=FastAPI()
    app.include_router(
        create_auth_router(
            Settings(),
            lambda:True,
            lambda:'Demo',
            lambda:'',
        )
    )
    client=TestClient(app)
    page=client.get('/login')
    assert page.status_code==200
    assert 'Demo' in page.text

    bad=client.post('/login',data={'user':'admin','password':'wrong'})
    assert bad.status_code==401

    good=client.post('/login',data={'user':'admin','password':'admin123'},follow_redirects=False)
    assert good.status_code==303
    assert good.headers['location']=='/'
    assert good.cookies

    out=client.get('/logout',follow_redirects=False)
    assert out.status_code==303
    assert out.headers['location']=='/login'
