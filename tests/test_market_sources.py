from decimal import Decimal
from pathlib import Path
import tempfile

from app.market_sources import _extract_html, _extract_json, build_consensus
from app.store import Store
from app.config import Settings


def test_html_auto_extracts_currency_buy_sell():
    html='<html><body><h2>USD Dólar</h2><div>Compra 26.9000 Venta 27.0500</div><h2>EUR Euro</h2><div>Compra 30.1000 Venta 33.9000</div></body></html>'
    r=_extract_html(html,{'mode':'AUTO','currencies':['USD','EUR']})
    assert r['USD']['sell']==Decimal('27.0500')
    assert r['EUR']['buy']==Decimal('30.1000')


def test_api_json_auto_extracts_common_paths():
    data={'rates':{'USD':{'buy':26.9,'sell':27.05},'EUR':{'buy':30.1,'sell':33.9}}}
    r=_extract_json(data,{'mode':'AUTO','currencies':['USD','EUR']})
    assert r['USD']['sell']==Decimal('27.05')
    assert r['EUR']['buy']==Decimal('30.1')


def test_store_requires_and_persists_dynamic_sources():
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db')
        sid=st.upsert_bank_source(source_id=None,code='BANK1',name='Banco Uno',country='GT',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{"mode":"AUTO","currencies":["USD"]}')
        row=st.get_bank_source(sid)
        assert row['code']=='BANK1' and row['source_type']=='WEB_HTML'


def test_consensus_requires_three_sources(monkeypatch):
    import app.market_sources as ms
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db')
        for code in ('A','B'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='X',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{}')
        company={'primary_bank':'A','bank_source_codes':'A,B'}
        c=build_consensus(st,Settings(),company,['USD'])
        assert not c.safe and any('3 fuentes' in w for w in c.warnings)

def test_consensus_three_sources_accepts_official_near_median(monkeypatch):
    import app.market_sources as ms
    from app.market_sources import SourceSnapshot
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db')
        for code in ('A','B','C'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='X',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{}')
        vals={'A':Decimal('27.0270'),'B':Decimal('27.0200'),'C':Decimal('27.0300')}
        def fake(src,settings):
            v=vals[src['code']]
            return SourceSnapshot(src['code'],src['name'],src['source_type'],src['url'],'2026-10-05T06:00:00-06:00',{'USD':{'buy':v-Decimal('.1'),'sell':v}},'x')
        monkeypatch.setattr(ms,'fetch_source',fake)
        c=ms.build_consensus(st,Settings(),{'primary_bank':'A','bank_source_codes':'A,B,C'},['USD'])
        assert c.safe and c.official_rates['USD']==Decimal('27.0270')


def test_consensus_blocks_outlier_official(monkeypatch):
    import app.market_sources as ms
    from app.market_sources import SourceSnapshot
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db'); st.set_settings({'max_source_deviation_percent':'1.0'})
        for code in ('A','B','C'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='X',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{}')
        vals={'A':Decimal('30.0000'),'B':Decimal('27.0200'),'C':Decimal('27.0300')}
        def fake(src,settings):
            v=vals[src['code']]
            return SourceSnapshot(src['code'],src['name'],src['source_type'],src['url'],'2026-10-05T06:00:00-06:00',{'USD':{'buy':v-Decimal('.1'),'sell':v}},'x')
        monkeypatch.setattr(ms,'fetch_source',fake)
        c=ms.build_consensus(st,Settings(),{'primary_bank':'A','bank_source_codes':'A,B,C'},['USD'])
        assert not c.safe and any('fuente oficial difiere' in w for w in c.warnings)

def test_bank_source_web_crud_and_preview(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as m
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'web.db'); st.set_settings({'setup_complete':'true','organization_name':'Demo'})
        monkeypatch.setattr(m,'store',st)
        m.settings.web_admin_user='admin'; m.settings.web_admin_password_hash=m.password_hash('admin123'); m.settings.web_session_secret='z'*48
        client=TestClient(m.app)
        login=client.post('/login',data={'user':'admin','password':'admin123'},follow_redirects=False)
        cookie=login.cookies.get(m.COOKIE); headers={'cookie':f'{m.COOKIE}={cookie}'}
        monkeypatch.setattr(
            m,'fetch_source',
            lambda src,settings: __import__('types').SimpleNamespace(
                code=src['code'],
                rates={'USD':{'buy':Decimal('26.90'),'sell':Decimal('27.02')}},
            ),
        )
        r=client.post('/banks/save',headers=headers,data={'code':'BANKX','name':'Banco X','country':'CR','source_type':'WEB_HTML','url':'https://bank.test/fx','config_json':'{"mode":"AUTO","currencies":["USD"]}','headers_json':'{}','timeout_seconds':'10','enabled':'on','tls_verify':'on'},follow_redirects=False)
        assert r.status_code==303
        assert st.get_bank_source_by_code('BANKX')['last_status']=='OK'
        monkeypatch.setattr(m,'scan_source',lambda src,settings:{'name':'Banco X','source_url':'https://bank.test/fx','rates':{'USD':{'buy':'500','sell':'510'}}})
        p=client.post('/banks/preview',headers=headers,data={'code':'BANKX','name':'Banco X','country':'CR','source_type':'WEB_HTML','url':'https://bank.test/fx','config_json':'{"mode":"AUTO","currencies":["USD"]}','headers_json':'{}','timeout_seconds':'10','tls_verify':'on'})
        assert p.status_code==200 and '510' in p.text and 'Extracción correcta' in p.text


def test_consensus_rejects_sell_below_buy(monkeypatch):
    import app.market_sources as ms
    from app.market_sources import SourceSnapshot
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db')
        for code in ('A','B','C'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='X',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{}')
        def fake(src,settings):
            if src['code']=='B':
                pair={'buy':Decimal('28.00'),'sell':Decimal('27.00')}
            else:
                pair={'buy':Decimal('26.90'),'sell':Decimal('27.02')}
            return SourceSnapshot(src['code'],src['name'],src['source_type'],src['url'],'2026-10-05T06:00:00-06:00',{'USD':pair},'x')
        monkeypatch.setattr(ms,'fetch_source',fake)
        c=ms.build_consensus(st,Settings(),{'primary_bank':'A','bank_source_codes':'A,B,C'},['USD'])
        assert not c.safe
        assert 'B' in c.failed_sources
        assert 'menor que compra' in c.failed_sources['B']


def test_consensus_rejects_implausible_pair_spread(monkeypatch):
    import app.market_sources as ms
    from app.market_sources import SourceSnapshot
    with tempfile.TemporaryDirectory() as d:
        st=Store(Path(d)/'x.db')
        st.set_settings({'max_pair_spread_percent':'10'})
        for code in ('A','B','C'):
            st.upsert_bank_source(source_id=None,code=code,name=code,country='X',source_type='WEB_HTML',url='https://example.com',enabled=True,config_json='{}')
        def fake(src,settings):
            pair={'buy':Decimal('20.00'),'sell':Decimal('30.00')} if src['code']=='C' else {'buy':Decimal('26.90'),'sell':Decimal('27.02')}
            return SourceSnapshot(src['code'],src['name'],src['source_type'],src['url'],'2026-10-05T06:00:00-06:00',{'USD':pair},'x')
        monkeypatch.setattr(ms,'fetch_source',fake)
        c=ms.build_consensus(st,Settings(),{'primary_bank':'A','bank_source_codes':'A,B,C'},['USD'])
        assert not c.safe
        assert 'C' in c.failed_sources
        assert 'spread compra/venta' in c.failed_sources['C']
