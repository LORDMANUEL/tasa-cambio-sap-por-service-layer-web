from pathlib import Path
from decimal import Decimal
from datetime import date
import tempfile
import requests
from app.store import Store
from app.policy import decide_rate_action
from app.web_auth import password_hash,verify_password,sign_session,verify_session
from app.sap_client import SapFxClient,SapCompany
from app.bank_registry import automatic_banks,BANKS
from app.notifications import recipients_from_text


def add_company(st, **kw):
    d=dict(company_id=None,company_name='Empresa',database_name='SBODEMO',db_type='HANA',environment='TEST',enabled=True,allow_write=True,scheduled_write=True,auto_enabled=True,schedule_hour=6,schedule_minute=0,use_usd=True,use_eur=True,sap_user='manager',primary_bank='BANPAIS',secondary_bank='FICOHSA',service_layer_root='',odata_version='',sap_b1_version='10.0')
    d.update(kw); return st.upsert_company(**d)

def test_fresh_install_has_no_vendor_specific_companies():
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db')
        assert st.list_companies()==[]
        assert st.get_settings()['organization_name']=='Mi Empresa'
        assert st.get_settings()['setup_complete']=='false'

def test_company_supports_multitenant_service_layer_fields():
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db'); cid=add_company(st,service_layer_root='https://sap2.local:50000/b1s',odata_version='v1',db_type='SQLSERVER')
        r=st.get_company(cid)
        assert r['service_layer_root'].endswith('/b1s') and r['odata_version']=='v1' and r['db_type']=='SQLSERVER'

def test_policy_bank_authoritative_decimal():
    assert decide_rate_action(Decimal('0'),Decimal('27.0270')).action=='CREATE'
    assert decide_rate_action(Decimal('27.0000'),Decimal('27.0270')).action=='UPDATE'
    assert decide_rate_action(Decimal('27.027000'),Decimal('27.0270')).action=='MATCH'

def test_web_auth_hash_and_session():
    h=password_hash('Clave123!'); assert verify_password('Clave123!',h); assert not verify_password('x',h)
    t=sign_session('admin','x'*40,ttl=60); assert verify_session(t,'x'*40,'admin')

def test_bank_catalog_keeps_validated_automatic_connectors():
    assert automatic_banks()==['BANPAIS','FICOHSA']
    assert len(BANKS)>=16 and BANKS['BCH']['status']=='REFERENCIA'

def test_recipient_list_parser():
    assert recipients_from_text('a@x.com, b@y.com; c@z.com\nd@w.com')==['a@x.com','b@y.com','c@z.com','d@w.com']

def test_prod_client_write_guard():
    c=SapFxClient('https://example.invalid/b1s/v2',SapCompany('PROD','PROD',False),'u','p',verify_tls=False); c.logged_in=True
    try: c.set_currency_rate('USD',date.today(),Decimal('27.1')); assert False
    except Exception as exc: assert 'BLOQUEADA' in str(exc)

def test_sap_get_rate_and_minus4006():
    c=SapFxClient('https://sap.invalid/b1s/v2',SapCompany('TEST','TEST',True),'u','p',verify_tls=False); c.logged_in=True
    ok=requests.Response(); ok.status_code=200; ok._content=b'27.027000'; ok.headers['Content-Type']='application/json'
    missing=requests.Response(); missing.status_code=400; missing._content=b'{"error":{"code":"-4006","message":"Update the exchange rate"}}'; missing.headers['Content-Type']='application/json'
    c.session.get=lambda *a,**k:ok; assert c.get_currency_rate('USD',date(2026,10,2))==Decimal('27.027000')
    c.session.get=lambda *a,**k:missing; assert c.get_currency_rate('EUR',date(2026,10,2))==Decimal('0')

def test_per_company_effective_endpoint(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db'); st.set_settings({'service_layer_root':'https://global.local:50000/b1s','odata_version':'v2'})
        cid=add_company(st,database_name='A',service_layer_root='https://tower.local:50000/b1s/v2',odata_version='v1')
        assert se._sap_url(Settings(),st,st.get_company(cid))=='https://tower.local:50000/b1s/v1'
        cid2=add_company(st,database_name='B',service_layer_root='',odata_version='')
        assert se._sap_url(Settings(),st,st.get_company(cid2))=='https://global.local:50000/b1s/v2'

def test_v5_visual_system_and_setup_builder_present():
    from app.config import BASE_DIR,Settings
    css=(BASE_DIR/'app/static/styles.css').read_text(encoding='utf-8'); js=(BASE_DIR/'app/static/app.js').read_text(encoding='utf-8'); main=(BASE_DIR/'app/main.py').read_text(encoding='utf-8')
    assert 'process-workflow-card' in css and '.setup-shell' in css and '.kpi-grid' in css
    assert 'data-add-company' in js and 'RECORRIDO GUIADO' in js and 'Trayendo datos del banco oficial' in js
    assert "@app.get('/setup'" in main and 'same_sap_credentials' in main and 'smtp_host' in main
    assert Settings().app_name=='Atas V5'

def test_health_and_setup_page(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as m
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'web.db'); monkeypatch.setattr(m,'store',st); client=TestClient(m.app)
        assert client.get('/health').status_code==200
        r=client.get('/setup'); assert r.status_code==200 and 'Configuración inicial' in r.text and 'Bases SAP / Multiempresa' in r.text
        assert client.get('/',follow_redirects=False).status_code==303

def test_full_setup_multi_company_and_navigation(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as m
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'setup.db'); monkeypatch.setattr(m,'store',st); monkeypatch.setattr(m,'_set_env_value',lambda k,v:None)
        m.settings.web_session_secret='s'*48
        client=TestClient(m.app)
        data={
          'organization_name':'Empresa Demo','admin_user':'admin5','admin_password':'Clave123!',
          'service_layer_root':'https://sap1.local:50000/b1s/v2','odata_version':'v2','sap_b1_version':'10.0',
          'same_sap_credentials':'on','shared_sap_user':'manager','shared_sap_password':'Sap123!',
          'company_name':['Empresa A','Empresa B'],'db_type':['HANA','SQLSERVER'],'database_name':['SBO_A','SBO_B'],
          'environment':['TEST','PROD'],'company_service_root':['','https://sap2.local:50000/b1s'],'company_odata':['','v1'],
          'sap_user':['',''],'sap_password':['',''],'schedule_time':'07:30','currencies_csv':'USD,EUR','primary_bank':'BANK1',
          'source_code':['BANK1','BANK2','BANK3'],'source_name':['Banco 1','Banco 2','Banco 3'],'source_country':['HN','HN','HN'],
          'source_type':['WEB_HTML','WEB_HTML','WEB_HTML'],'source_url':['https://one.test','https://two.test','https://three.test'],
          'source_config':['{"mode":"AUTO","currencies":["USD","EUR"]}']*3
        }
        monkeypatch.setattr(m,'fetch_source',lambda src,settings: object())
        r=client.post('/setup',data=data,follow_redirects=False)
        assert r.status_code==303 and r.headers['location']=='/?welcome=1'
        rows=st.list_companies(); assert len(rows)==2
        b=next(x for x in rows if x['database_name']=='SBO_B')
        assert b['db_type']=='SQLSERVER' and b['service_layer_root']=='https://sap2.local:50000/b1s' and b['odata_version']=='v1'
        cookie=r.cookies.get(m.COOKIE); headers={'cookie':f'{m.COOKIE}={cookie}'}
        for path in ('/','/companies','/automation','/banks','/transactions','/reports','/settings','/logs','/health'):
            rr=client.get(path,headers=headers,follow_redirects=False); assert rr.status_code==200,(path,rr.status_code)


def test_release_has_no_customer_specific_defaults():
    """The public product must not ship customer-specific endpoints or CompanyDB names."""
    from app.config import BASE_DIR
    forbidden=('YUDE','129.80.108.0','TEST_SBO_YUDEMOTORS','SBO_YUDE','Z_TST_YUDE_5')
    scan_ext={'.py','.md','.txt','.example','.json','.js','.css','.html','.yml','.yaml','.ps1','.bat','.cmd','.sh','.iss','.service','.desktop'}
    offenders=[]
    for p in BASE_DIR.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '.venv' in p.parts or 'dist' in p.parts or 'tests' in p.parts:
            continue
        if p.suffix.lower() not in scan_ext and p.name not in ('.env.example',):
            continue
        txt=p.read_text(encoding='utf-8',errors='ignore')
        for token in forbidden:
            if token in txt:
                offenders.append((str(p.relative_to(BASE_DIR)),token))
    assert not offenders, f'Customer-specific data found: {offenders}'


def test_atas_release_identity_and_links():
    from app.config import BASE_DIR, Settings
    assert Settings().app_name=='Atas V5'
    readme=(BASE_DIR/'README.md').read_text(encoding='utf-8')
    site=(BASE_DIR/'site/index.html').read_text(encoding='utf-8')
    installer=(BASE_DIR/'installer/windows/Atas.iss').read_text(encoding='utf-8')
    assert 'Luis Manuel Fajardo Rivera' in readme
    assert 'https://github.com/LORDMANUEL' in readme
    assert '<title>Atas V5</title>' in site
    assert 'Luis Manuel Fajardo Rivera' in site
    assert '#define MyAppName "Atas"' in installer


def test_release_packaging_files_are_present():
    from app.config import BASE_DIR
    required=[
        'ATAS.bat',
        'scripts/windows/start-atas.cmd',
        'installer/windows/Atas.iss',
        'packaging/debian/atas',
        'packaging/debian/atas.desktop',
        'packaging/debian/atas.service',
        'scripts/build_deb.sh',
        '.github/workflows/build-installers.yml',
        '.github/workflows/publish-pages.yml',
        'docs/V4_V5_DIFERENCIAS.md',
    ]
    assert all((BASE_DIR/p).exists() for p in required)


def test_daily_scheduler_claim_is_atomic():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'scheduler.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True,schedule_hour=0,schedule_minute=0)
        day=datetime.now(ZoneInfo('America/Tegucigalpa')).date().isoformat()
        assert st.claim_daily_run(cid,day) is True
        assert st.claim_daily_run(cid,day) is False
        row=st.get_company(cid)
        assert row['last_run_date']==day
        assert row['last_run_status']=='RUNNING'


def test_daily_scheduler_runs_company_only_once(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'scheduler.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True,schedule_hour=0,schedule_minute=0)
        calls=[]
        def fake_reconcile(settings,store,company_id,scheduled=True):
            calls.append(company_id)
            return {'company':'SBODEMO','rates':{'USD':{'status':'MATCH'}}}
        monkeypatch.setattr(se,'reconcile_company',fake_reconcile)
        first=se.run_due_schedules(Settings(),st)
        second=se.run_due_schedules(Settings(),st)
        assert len(first)==1
        assert second==[]
        assert calls==[cid]
        assert st.get_company(cid)['last_run_status']=='OK'


def test_daily_scheduler_claim_survives_unexpected_failure(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'scheduler.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True,schedule_hour=0,schedule_minute=0)
        def boom(*args,**kwargs):
            raise RuntimeError('simulated scheduler crash')
        monkeypatch.setattr(se,'reconcile_company',boom)
        first=se.run_due_schedules(Settings(),st)
        second=se.run_due_schedules(Settings(),st)
        assert len(first)==1 and first[0]['error']=='simulated scheduler crash'
        assert second==[]
        row=st.get_company(cid)
        assert row['last_run_status']=='ERROR'
