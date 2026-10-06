from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta
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
        monkeypatch.setattr(
            m,'fetch_source',
            lambda src,settings: __import__('types').SimpleNamespace(
                code=src['code'],
                rates={
                    'USD':{'buy':Decimal('26.90'),'sell':Decimal('27.02')},
                    'EUR':{'buy':Decimal('30.10'),'sell':Decimal('33.90')},
                },
            ),
        )
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
        assert row['scheduler_claim_date']==day
        assert row['last_run_date'] is None
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


def test_scheduler_does_not_duplicate_pre_recorded_error(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'scheduler.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True,schedule_hour=0,schedule_minute=0)
        def fake_reconcile(settings,store,company_id,scheduled=True):
            row=store.get_company(company_id)
            se.record_system_error(store,row,'already recorded','reconcile')
            return {'company':row['database_name'],'rates':{},'error':'already recorded','error_recorded':True}
        monkeypatch.setattr(se,'reconcile_company',fake_reconcile)
        out=se.run_due_schedules(Settings(),st)
        assert len(out)==1
        errors=[x for x in st.list_transactions(20) if x['status']=='ERROR']
        assert len(errors)==1
        assert errors[0]['decision']=='RECONCILE'


def test_version_file_is_single_source_of_truth():
    from app.config import BASE_DIR
    from app.version import get_version
    expected=(BASE_DIR/'VERSION.txt').read_text(encoding='utf-8').strip()
    assert get_version()==expected
    import app.main as m
    assert m.health()['version']==expected


def test_packaging_versions_are_not_hardcoded_to_500():
    from app.config import BASE_DIR
    installer=(BASE_DIR/'installer/windows/Atas.iss').read_text(encoding='utf-8')
    workflow=(BASE_DIR/'.github/workflows/build-installers.yml').read_text(encoding='utf-8')
    deb=(BASE_DIR/'scripts/build_deb.sh').read_text(encoding='utf-8')
    assert '#define MyAppVersion AppVersion' in installer
    assert 'OutputBaseFilename=Atas-V{#MyAppVersion}-Setup-x64' in installer
    assert 'VERSION.txt' in workflow
    assert 'VERSION=5.0.0 ./scripts/build_deb.sh' not in workflow
    assert 'version=5.0.0' not in workflow
    assert 'VERSION.txt' in deb


def test_run_status_prioritizes_blocked_over_match():
    import app.sync_engine as se
    status,message=se._run_status({'rates':{
        'USD':{'status':'MATCH'},
        'EUR':{'status':'UPDATE_WRITE_BLOCKED'},
    }})
    assert status=='BLOCKED'
    assert 'UPDATE_WRITE_BLOCKED' in message


def test_reconcile_records_bank_validation_failure_once(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'audit.db')
        cid=add_company(st,bank_source_codes='A,B,C',primary_bank='A',secondary_bank='B')
        fake=SimpleNamespace(
            safe=False,
            warnings=['simulated unsafe consensus'],
            official_rates={},
            successful_sources=['A','B','C'],
            failed_sources={},
            notices=[],
        )
        monkeypatch.setattr(se,'_comparison',lambda settings,store,row:fake)
        result=se.reconcile_company(Settings(),st,cid,scheduled=True)
        assert result['error']=='BANK_VALIDATION_FAILED'
        assert result['error_recorded'] is True
        errors=[x for x in st.list_transactions(20) if x['status']=='ERROR']
        assert len(errors)==1
        assert errors[0]['decision']=='BANK-VALIDATION'


def test_reconcile_records_missing_credentials_once(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'audit.db')
        cid=add_company(st,bank_source_codes='A,B,C',primary_bank='A',secondary_bank='B')
        fake=SimpleNamespace(
            safe=True,
            warnings=[],
            official_rates={'USD':Decimal('27.02'),'EUR':Decimal('33.90')},
            successful_sources=['A','B','C'],
            failed_sources={},
            notices=[],
        )
        monkeypatch.setattr(se,'_comparison',lambda settings,store,row:fake)
        result=se.reconcile_company(Settings(),st,cid,scheduled=True)
        assert result['error']=='SAP_PASSWORD_NOT_CONFIGURED'
        assert result['error_recorded'] is True
        errors=[x for x in st.list_transactions(20) if x['status']=='ERROR']
        assert len(errors)==1
        assert errors[0]['decision']=='CREDENTIALS'


def test_sap_odata_v1_uses_post_function_import():
    c=SapFxClient('https://sap.invalid/b1s/v1',SapCompany('TEST','TEST',True),'u','p',verify_tls=False)
    c.logged_in=True
    ok=requests.Response(); ok.status_code=200; ok._content=b'27.027000'; ok.headers['Content-Type']='application/json'
    calls={}
    def fake_post(url,**kwargs):
        calls['url']=url
        calls['json']=kwargs.get('json')
        return ok
    c.session.post=fake_post
    value=c.get_currency_rate('USD',date(2026,10,2))
    assert value==Decimal('27.027000')
    assert calls['url'].endswith('/v1/SBOBobService_GetCurrencyRate')
    assert calls['json']=={'Currency':'USD','Date':'20261002'}


def test_sap_odata_v1_minus4006_is_missing_rate():
    c=SapFxClient('https://sap.invalid/b1s/v1',SapCompany('TEST','TEST',True),'u','p',verify_tls=False)
    c.logged_in=True
    missing=requests.Response(); missing.status_code=400
    missing._content=b'{"error":{"code":"-4006","message":"Update the exchange rate"}}'
    missing.headers['Content-Type']='application/json'
    c.session.post=lambda *a,**k:missing
    assert c.get_currency_rate('EUR',date(2026,10,2))==Decimal('0')


def test_sap_set_rate_rejects_invalid_currency_code():
    c=SapFxClient('https://sap.invalid/b1s/v2',SapCompany('TEST','TEST',True),'u','p',verify_tls=False)
    c.logged_in=True
    try:
        c.set_currency_rate("USD'BAD",date(2026,10,2),Decimal('27.1'))
        assert False
    except Exception as exc:
        assert 'Código de moneda inválido' in str(exc)


def test_main_settings_routes_are_not_duplicated():
    from app.config import BASE_DIR
    text=(BASE_DIR/'app/main.py').read_text(encoding='utf-8')
    assert text.count("async def _save_notification_form")==1
    assert text.count("@app.post('/settings/notifications')")==1
    assert text.count("@app.get('/logs'")==1
    assert text.count("@app.get('/health')")==1


def test_company_invalid_schedule_returns_400_not_500(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as m
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'web.db')
        st.set_settings({'setup_complete':'true','organization_name':'Demo'})
        for code in ('A','B','C'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='HN',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{}')
        monkeypatch.setattr(m,'store',st)
        m.settings.web_admin_user='admin'
        m.settings.web_admin_password_hash=m.password_hash('admin123')
        m.settings.web_session_secret='z'*48
        client=TestClient(m.app)
        login=client.post('/login',data={'user':'admin','password':'admin123'},follow_redirects=False)
        cookie=login.cookies.get(m.COOKIE)
        headers={'cookie':f'{m.COOKIE}={cookie}'}
        r=client.post('/companies/save',headers=headers,data={
            'company_name':'Demo','database_name':'SBO_DEMO','db_type':'HANA','environment':'TEST',
            'sap_user':'manager','schedule_time':'99:99','primary_bank':'A',
            'bank_sources':['A','B','C'],'currencies_csv':'USD','enabled':'on'
        })
        assert r.status_code==400
        assert 'Hora inválida' in r.text


def test_setup_can_reuse_preexisting_sources_after_partial_attempt(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as m
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'setup.db')
        for code in ('BANK1','BANK2','BANK3'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='HN',source_type='WEB_HTML',url=f'https://{code.lower()}.test',enabled=True,config_json='{"mode":"AUTO","currencies":["USD"]}')
        monkeypatch.setattr(m,'store',st)
        monkeypatch.setattr(m,'_set_env_value',lambda k,v:None)
        monkeypatch.setattr(
            m,'fetch_source',
            lambda src,settings: __import__('types').SimpleNamespace(
                code=src['code'],
                rates={
                    'USD':{'buy':Decimal('26.90'),'sell':Decimal('27.02')},
                    'EUR':{'buy':Decimal('30.10'),'sell':Decimal('33.90')},
                },
            ),
        )
        m.settings.web_session_secret='s'*48
        client=TestClient(m.app)
        data={
          'organization_name':'Empresa Demo','admin_user':'admin5','admin_password':'Clave123!',
          'service_layer_root':'https://sap1.local:50000/b1s','odata_version':'v2','sap_b1_version':'10.0',
          'same_sap_credentials':'on','shared_sap_user':'manager','shared_sap_password':'Sap123!',
          'company_name':['Empresa A'],'db_type':['HANA'],'database_name':['SBO_A'],
          'environment':['TEST'],'company_service_root':[''],'company_odata':[''],
          'sap_user':[''],'sap_password':[''],'schedule_time':'07:30','currencies_csv':'USD','primary_bank':'BANK1',
          'source_code':['BANK1','BANK2','BANK3'],'source_name':['Banco 1','Banco 2','Banco 3'],'source_country':['HN','HN','HN'],
          'source_type':['WEB_HTML','WEB_HTML','WEB_HTML'],
          'source_url':['https://bank1.test','https://bank2.test','https://bank3.test'],
          'source_config':['{"mode":"AUTO","currencies":["USD"]}']*3
        }
        r=client.post('/setup',data=data,follow_redirects=False)
        assert r.status_code==303
        assert len(st.list_bank_sources())==3
        assert len(st.list_companies())==1


def test_smtp_test_does_not_claim_success_when_notifications_disabled(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as m
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'web.db')
        st.set_settings({'setup_complete':'true','organization_name':'Demo','notifications_enabled':'false'})
        monkeypatch.setattr(m,'store',st)
        m.settings.web_admin_user='admin'
        m.settings.web_admin_password_hash=m.password_hash('admin123')
        m.settings.web_session_secret='z'*48
        client=TestClient(m.app)
        login=client.post('/login',data={'user':'admin','password':'admin123'},follow_redirects=False)
        cookie=login.cookies.get(m.COOKIE)
        headers={'cookie':f'{m.COOKIE}={cookie}'}
        r=client.post('/settings/notifications/test',headers=headers,data={
            'smtp_host':'smtp.example.com','smtp_port':'587','smtp_security':'STARTTLS',
            'smtp_user':'x@example.com','smtp_from':'x@example.com',
            'notification_recipients':'a@example.com'
        })
        assert r.status_code==400
        assert 'Active las notificaciones' in r.text


def test_company_supports_arbitrary_three_letter_currencies():
    import app.sync_engine as se
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'currencies.db')
        cid=add_company(
            st,
            use_usd=False,
            use_eur=False,
            currencies_csv='JPY,CHF',
            database_name='SBO_MULTI_CURRENCY',
        )
        row=st.get_company(cid)
        assert row['currencies_csv']=='JPY,CHF'
        assert se._currencies(row)==['JPY','CHF']


def test_company_rejects_invalid_currency_code():
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'currencies.db')
        try:
            add_company(st,use_usd=False,use_eur=False,currencies_csv='USDD',database_name='SBO_BAD_CUR')
            assert False
        except ValueError as exc:
            assert 'códigos de 3 letras' in str(exc)


def test_inspect_company_reads_sap_even_when_bank_consensus_is_unsafe(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    from types import SimpleNamespace

    class FakeSap:
        def __init__(self,*args,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def get_local_currency(self): return 'HNL'
        def get_currency_rate(self,cur,day): return Decimal('27.0000') if cur=='USD' else Decimal('33.0000')

    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'inspect.db')
        cid=add_company(st,bank_source_codes='A,B,C',primary_bank='A',secondary_bank='B')
        monkeypatch.setattr(se,'_password',lambda row:'pw')
        monkeypatch.setattr(se,'SapFxClient',FakeSap)
        monkeypatch.setattr(se,'_comparison',lambda settings,store,row:SimpleNamespace(
            safe=False,
            warnings=['simulated bank failure'],
            successful_sources=['A','B'],
            failed_sources={'C':'offline'},
            official_rates={},
        ))
        result=se.inspect_company(Settings(),st,cid)
        assert result.get('error') is None
        assert result['bank_error']=='BANK_VALIDATION_FAILED'
        assert result['rates']['USD']['sap']=='27.0000'
        assert result['rates']['USD']['bank'] is None
        assert result['rates']['USD']['can_test_write'] is False
        tx=st.list_transactions(10)
        assert any(x['status']=='READ_ONLY_BANK_BLOCKED' for x in tx)


def test_secret_filter_keeps_safe_password_status_but_redacts_values():
    import logging
    from app.logging_setup import SecretFilter
    f=SecretFilter()
    safe=logging.LogRecord('x',logging.INFO,'',0,'SAP_PASSWORD_NOT_CONFIGURED',(),None)
    assert f.filter(safe)
    assert safe.getMessage()=='SAP_PASSWORD_NOT_CONFIGURED'
    secret=logging.LogRecord('x',logging.INFO,'',0,'password=SuperSecret api_key:abc123',(),None)
    assert f.filter(secret)
    msg=secret.getMessage()
    assert 'SuperSecret' not in msg
    assert 'abc123' not in msg
    assert 'password=***' in msg


def test_debian_packaging_keeps_persistent_data_out_of_opt_payload():
    from app.config import BASE_DIR
    build=(BASE_DIR/'scripts/build_deb.sh').read_text(encoding='utf-8')
    post=(BASE_DIR/'packaging/debian/postinst').read_text(encoding='utf-8')
    assert "--exclude '/data'" in build
    assert "--exclude '/logs'" in build
    assert "--exclude '/app/static/uploads'" in build
    assert 'migrate_and_link "$APP/data" "$DATA"' in post
    assert 'migrate_and_link "$APP/logs" "$LOG"' in post
    assert 'migrate_and_link "$APP/app/static/uploads" "$DATA/uploads"' in post


def test_notification_classifies_blocked_run_as_attention():
    from app.notifications import _result_needs_attention
    assert _result_needs_attention({'rates':{'USD':{'status':'MATCH'},'EUR':{'status':'UPDATE_WRITE_BLOCKED'}}})
    assert not _result_needs_attention({'rates':{'USD':{'status':'MATCH'}}})


def test_notification_rejects_invalid_smtp_mode():
    from app.notifications import send_email, NotificationError
    from app.credential_store import encrypt_secret
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'smtp.db')
        st.set_settings({
            'notifications_enabled':'true','smtp_host':'smtp.example.com','smtp_port':'587',
            'smtp_security':'INVALID','smtp_user':'u@example.com','smtp_from':'u@example.com',
            'notification_recipients':'a@example.com','smtp_secret':encrypt_secret('secret')
        })
        try:
            send_email(st,'x','y')
            assert False
        except NotificationError as exc:
            assert 'Modo SMTP inválido' in str(exc)


def test_manual_reconcile_does_not_require_auto_enabled():
    import app.sync_engine as se
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'manual.db')
        cid=add_company(st,auto_enabled=False,allow_write=True,scheduled_write=False)
        row=st.get_company(cid)
        assert se._manual_reconcile_write_allowed(st,row) is True
        assert se._scheduled_write_allowed(st,row) is False


def test_manual_prod_reconcile_requires_global_and_company_write_gate():
    import app.sync_engine as se
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'manual.db')
        cid=add_company(st,database_name='PRODDB',environment='PROD',auto_enabled=False,scheduled_write=True,allow_write=False)
        row=st.get_company(cid)
        assert se._manual_reconcile_write_allowed(st,row) is False
        st.set_settings({'prod_automation_enabled':'true'})
        row=st.get_company(cid)
        assert se._manual_reconcile_write_allowed(st,row) is True
        assert se._scheduled_write_allowed(st,row) is False


def test_sap_tls_verification_can_be_configured_from_store():
    import app.sync_engine as se
    from app.config import Settings
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'tls.db')
        st.set_settings({'sap_verify_tls':'true'})
        assert se._sap_verify_tls(Settings(),st) is True
        st.set_settings({'sap_verify_tls':'false'})
        assert se._sap_verify_tls(Settings(),st) is False


def test_manual_result_date_does_not_claim_daily_scheduler():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'scheduler-separation.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True,schedule_hour=0,schedule_minute=0)
        day=datetime.now(ZoneInfo('America/Tegucigalpa')).date().isoformat()
        st.mark_run_result(cid,day,'OK','manual run')
        row=st.get_company(cid)
        assert row['last_run_date']==day
        assert row['scheduler_claim_date'] is None
        assert st.claim_daily_run(cid,day) is True


def test_scheduler_claim_migration_preserves_existing_last_run_date(tmp_path):
    import sqlite3
    # Use pytest's managed temp path instead of deleting the SQLite/WAL directory
    # immediately inside the test. Windows can briefly retain a SQLite file handle
    # after WAL/checkpoint activity even when every Python connection is closed.
    db=tmp_path/'old.db'
    st=Store(db)
    cid=add_company(st,database_name='MIGRATE_DB')
    st.mark_run_result(cid,'2026-10-05','OK','old version')
    con=sqlite3.connect(db)
    try:
        con.execute('UPDATE companies SET scheduler_claim_date=last_run_date WHERE id=?',(cid,))
        con.commit()
        con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    finally:
        con.close()
    row=st.get_company(cid)
    assert row['scheduler_claim_date']=='2026-10-05'


def test_recover_stale_running_preserves_claim():
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'stale.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True)
        day=datetime.now(ZoneInfo('America/Tegucigalpa')).date().isoformat()
        assert st.claim_daily_run(cid,day) is True
        old=(datetime.now(ZoneInfo('America/Tegucigalpa'))-timedelta(minutes=30)).isoformat()
        with st.conn() as con:
            con.execute("UPDATE companies SET last_run_at=? WHERE id=?",(old,cid))
        assert st.recover_stale_running(15)==1
        row=st.get_company(cid)
        assert row['last_run_status']=='INTERRUPTED'
        assert row['scheduler_claim_date']==day
        assert st.claim_daily_run(cid,day) is False


def test_legacy_noop_settings_removed():
    from app.config import BASE_DIR
    config=(BASE_DIR/'app/config.py').read_text(encoding='utf-8')
    env=(BASE_DIR/'.env.example').read_text(encoding='utf-8')
    main=(BASE_DIR/'app/main.py').read_text(encoding='utf-8')
    for name in ('app_host','app_api_key','sap_enabled','sap_allow_prod_write'):
        assert name not in config
    for name in ('APP_HOST','APP_API_KEY','SAP_ENABLED','SAP_ALLOW_PROD_WRITE'):
        assert name not in env
    assert 'from app.bank_registry import BANKS, automatic_banks' not in main


def test_reconcile_match_never_writes_same_rate_again(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    from app.credential_store import encrypt_secret
    from types import SimpleNamespace

    class FakeSap:
        writes=[]
        def __init__(self,*args,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def get_currency_rate(self,cur,day): return Decimal('27.0200')
        def set_currency_rate(self,cur,day,rate): self.writes.append((cur,day,rate))

    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'same-rate.db')
        cid=add_company(
            st,
            currencies_csv='USD',
            use_usd=True,
            use_eur=False,
            bank_source_codes='A,B,C',
            primary_bank='A',
            auto_enabled=True,
            scheduled_write=True,
        )
        st.set_secret_blob(cid, encrypt_secret('pw'))
        fake=SimpleNamespace(
            safe=True,
            warnings=[],
            notices=[],
            successful_sources=['A','B','C'],
            failed_sources={},
            official_rates={'USD':Decimal('27.0200')},
        )
        monkeypatch.setattr(se,'_comparison',lambda settings,store,row:fake)
        monkeypatch.setattr(se,'SapFxClient',FakeSap)

        result=se.reconcile_company(Settings(),st,cid,scheduled=True)

        assert result['rates']['USD']['status']=='MATCH'
        assert FakeSap.writes==[]


def test_scheduled_reconcile_waits_when_official_rate_equals_previous_day(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    from app.credential_store import encrypt_secret
    from types import SimpleNamespace

    class FailIfSapUsed:
        def __init__(self,*args,**kwargs):
            raise AssertionError('SAP must not be opened while every currency waits for bank refresh')

    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'previous-rate.db')
        cid=add_company(
            st,
            currencies_csv='USD',
            use_usd=True,
            use_eur=False,
            bank_source_codes='A,B,C',
            primary_bank='A',
        )
        st.set_secret_blob(cid, encrypt_secret('pw'))
        today=se._local_day(Settings())
        yesterday=(today-timedelta(days=1)).isoformat()
        st.record_market_snapshot(
            observed_day=yesterday,
            fetched_at=yesterday+'T06:00:00-06:00',
            source_code='A',
            source_name='A',
            source_url='https://example.com',
            rates={'USD':{'buy':Decimal('26.90'),'sell':Decimal('27.0200')}},
            raw_hash='old',
        )
        fake=SimpleNamespace(
            safe=True,warnings=[],notices=[],
            successful_sources=['A','B','C'],failed_sources={},
            official_rates={'USD':Decimal('27.0200')},
        )
        monkeypatch.setattr(se,'_comparison',lambda settings,store,row:fake)
        monkeypatch.setattr(se,'SapFxClient',FailIfSapUsed)

        result=se.reconcile_company(Settings(),st,cid,scheduled=True)

        assert result['retry_required'] is True
        assert result['retry_after_minutes']==60
        assert result['rates']['USD']['status']=='WAITING_BANK_UPDATE'


def test_manual_reconcile_is_not_blocked_by_same_previous_day_rate(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings
    from app.credential_store import encrypt_secret
    from types import SimpleNamespace

    class FakeSap:
        writes=[]
        def __init__(self,*args,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def get_currency_rate(self,cur,day): return Decimal('0')
        def set_currency_rate(self,cur,day,rate): self.writes.append((cur,rate))

    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'manual-previous.db')
        cid=add_company(st,currencies_csv='USD',use_usd=True,use_eur=False,primary_bank='A')
        st.set_secret_blob(cid, encrypt_secret('pw'))
        today=se._local_day(Settings())
        yesterday=(today-timedelta(days=1)).isoformat()
        st.record_market_snapshot(
            observed_day=yesterday,
            fetched_at=yesterday+'T06:00:00-06:00',
            source_code='A',source_name='A',source_url='https://example.com',
            rates={'USD':{'buy':Decimal('26.90'),'sell':Decimal('27.0200')}},
            raw_hash='old',
        )
        fake=SimpleNamespace(
            safe=True,warnings=[],notices=[],
            successful_sources=['A','B','C'],failed_sources={},
            official_rates={'USD':Decimal('27.0200')},
        )
        monkeypatch.setattr(se,'_comparison',lambda settings,store,row:fake)
        monkeypatch.setattr(se,'SapFxClient',FakeSap)

        result=se.reconcile_company(Settings(),st,cid,scheduled=False)

        assert result.get('retry_required') is None
        assert result['rates']['USD']['status']=='CREATED_VERIFIED'
        assert FakeSap.writes


def test_scheduler_releases_claim_and_waits_one_hour(monkeypatch):
    import app.sync_engine as se
    from app.config import Settings

    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'retry.db')
        cid=add_company(st,auto_enabled=True,scheduled_write=True,schedule_hour=0,schedule_minute=0)

        monkeypatch.setattr(
            se,
            'reconcile_company',
            lambda *args,**kwargs: {
                'company':'SBODEMO',
                'rates':{'USD':{'status':'WAITING_BANK_UPDATE'}},
                'retry_required':True,
                'retry_after_minutes':60,
            },
        )

        first=se.run_due_schedules(Settings(),st)
        assert len(first)==1
        row=st.get_company(cid)
        assert row['scheduler_claim_date'] is None
        assert row['last_run_status']=='WAITING_BANK_UPDATE'
        assert row['scheduler_next_retry_at']
        assert row['scheduler_retry_count']==1

        second=se.run_due_schedules(Settings(),st)
        assert second==[]


def test_previous_market_observation_ignores_same_day(tmp_path):
    st=Store(tmp_path/'previous.db')
    st.record_market_snapshot(
        observed_day='2026-10-05',
        fetched_at='2026-10-05T06:00:00-06:00',
        source_code='A',source_name='A',source_url='https://example.com',
        rates={'USD':{'buy':'26.90','sell':'27.01'}},
        raw_hash='old',
    )
    st.record_market_snapshot(
        observed_day='2026-10-06',
        fetched_at='2026-10-06T06:00:00-06:00',
        source_code='A',source_name='A',source_url='https://example.com',
        rates={'USD':{'buy':'26.91','sell':'27.02'}},
        raw_hash='new',
    )
    previous=st.previous_market_observation('A','USD','2026-10-06')
    assert previous['observed_day']=='2026-10-05'
    assert previous['sell']=='27.01'
