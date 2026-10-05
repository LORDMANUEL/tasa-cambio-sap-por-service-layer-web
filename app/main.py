"""Atas V5 - generic, local-first accounting platform.

V5 keeps the proven SAP/bank engine from the V4 line and replaces the
company-specific presentation/configuration with a reusable first-run wizard,
per-company Service Layer overrides, optional outgoing email notifications and
custom branding.
"""
from __future__ import annotations
import csv, io, logging, os, re, threading, time, secrets
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.logging_setup import configure_logging
from app.store import Store
from app.credential_store import encrypt_secret
from app.web_auth import COOKIE, sign_session, verify_session, verify_password, password_hash
from app.dashboard import layout, esc, badge, page_header
from app.bank_registry import BANKS, automatic_banks
from app.providers import get_provider
from app.market_sources import fetch_source, scan_source, MarketSourceError
from app.sync_engine import inspect_company, write_suggested_manual, run_due_schedules, reconcile_company
from app.notifications import send_email, send_run_summary, recipients_from_text
from app.version import get_version

settings=get_settings(); configure_logging(settings); log=logging.getLogger(__name__)
store=Store(settings.db_path,settings.timezone)
ROOT=Path(__file__).resolve().parent.parent
UPLOAD_DIR=ROOT/'app'/'static'/'uploads'; UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
_stop=threading.Event(); _thread=None


def _authed(req:Request): return verify_session(req.cookies.get(COOKIE),settings.web_session_secret,settings.web_admin_user)
def _redirect_login(): return RedirectResponse('/login',303)
def _cfg(): return store.get_settings()
def _setup_complete(): return _cfg().get('setup_complete','false').lower()=='true'
def _org(): return _cfg().get('organization_name','Mi Empresa') or 'Mi Empresa'
def _logo_url(): return _cfg().get('organization_logo','')
def _ui(title, body): return layout(title,body,organization=_org(),logo_url=_logo_url())

def _set_env_value(key:str,value:str)->None:
    env=ROOT/'.env'; lines=env.read_text(encoding='utf-8').splitlines() if env.exists() else []; out=[]; found=False
    for line in lines:
        if line.startswith(key+'='): out.append(f'{key}={value}'); found=True
        else: out.append(line)
    if not found: out.append(f'{key}={value}')
    env.write_text('\n'.join(out)+'\n',encoding='utf-8')

def _endpoint(root:str, version:str)->str:
    root=re.sub(r'/v\d+$','',str(root or '').strip().rstrip('/'),flags=re.I)
    version=(version or 'v2').strip().lower()
    return f'{root}/{version}' if root else ''

def _effective_company_endpoint(c:dict)->str:
    cfg=_cfg(); return _endpoint(c.get('service_layer_root') or cfg.get('service_layer_root',''), c.get('odata_version') or cfg.get('odata_version','v2'))

def _save_logo(upload:UploadFile|None)->str:
    if not upload or not upload.filename: return ''
    ext=Path(upload.filename).suffix.lower()
    if ext not in {'.png','.jpg','.jpeg','.webp'}: raise ValueError('Logo debe ser PNG, JPG/JPEG o WEBP.')
    data=upload.file.read()
    if len(data)>3*1024*1024: raise ValueError('Logo supera 3 MB.')
    name='company_logo'+ext
    for old in UPLOAD_DIR.glob('company_logo.*'): old.unlink(missing_ok=True)
    (UPLOAD_DIR/name).write_bytes(data)
    return '/static/uploads/'+name

def _scheduler_loop():
    while not _stop.wait(30):
        try:
            results=run_due_schedules(settings,store)
            if results:
                log.info('V5 scheduler executed companies=%s',len(results))
                send_run_summary(store,results)
            store.cleanup(int(_cfg().get('log_retention_days','30')))
        except Exception: log.exception('V5 scheduler failed')

@asynccontextmanager
async def lifespan(app):
    global _thread
    _stop.clear(); _thread=threading.Thread(target=_scheduler_loop,name='sap-fx-v5-scheduler',daemon=True); _thread.start(); yield
    _stop.set()
    if _thread and _thread.is_alive(): _thread.join(timeout=2)

app=FastAPI(title='Atas V5',version='5.0.0',lifespan=lifespan,docs_url=None)
app.mount('/static',StaticFiles(directory=str(ROOT/'app'/'static')),name='static')

@app.middleware('http')
async def headers(req,call_next):
    r=await call_next(req)
    r.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'no-referrer','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'"})
    return r

# ---------------------------------------------------------------------------
# First-run wizard
# ---------------------------------------------------------------------------
def _setup_page(error:str='')->str:
    error_html=f"<div class='setup-error'>{esc(error)}</div>" if error else ''
    body=f"""
<div class='setup-shell'>
  <aside class='setup-side'>
    <div class='setup-product'><div class='brand-mark xl'>AT</div><div><strong>SAP FX</strong><span>Control Center V5</span></div></div>
    <div class='setup-hero-art'><div class='server-stack'><i></i><i></i><i></i><b>SAP</b></div></div>
    <h1>Bienvenido a Atas</h1>
    <p>Configura una vez y deja lista la plataforma para consultar bancos, comparar SAP, automatizar tasas y conservar auditoría.</p>
    <div class='setup-side-status'><span class='status-dot'></span><b>Instalación local</b><small>Los datos y credenciales permanecen en esta PC.</small></div>
  </aside>
  <main class='setup-main'>
    <div class='setup-head'><div><div class='eyebrow'>CONFIGURACIÓN INICIAL</div><h2>Deja el sistema listo para operar</h2></div><span class='setup-chip'>Primera ejecución</span></div>
    <div class='setup-steps'><span class='active'>1 Empresa</span><span>2 Administrador</span><span>3 Notificaciones</span><span>4 Service Layer</span><span>5 Bases SAP</span><span>6 Fuentes</span><span>7 Automatización</span><span>8 Finalizar</span></div>
    {error_html}
    <form method='post' action='/setup' enctype='multipart/form-data' class='setup-form' data-process='Guardando configuración inicial'>
      <section class='setup-card' data-tour='empresa'><div class='step-no'>1</div><div class='setup-card-title'><h3>Información de la empresa</h3><p>Personaliza el panel. El logo y nombre aparecerán en toda la plataforma.</p></div>
        <div class='brand-config'><label class='logo-drop'><span>▧</span><b>Subir logo</b><small>PNG, JPG o WEBP · máx. 3 MB</small><input type='file' name='logo' accept='.png,.jpg,.jpeg,.webp'></label><div><label>Nombre de la empresa *</label><input name='organization_name' placeholder='Mi Empresa S.A.' required></div></div>
      </section>
      <section class='setup-card'><div class='step-no'>2</div><div class='setup-card-title'><h3>Cuenta de administrador web</h3><p>Acceso principal al panel local.</p></div>
        <div class='form-grid cols2'><div><label>Usuario administrador *</label><input name='admin_user' value='admin' required></div><div><label>Contraseña *</label><input type='password' name='admin_password' minlength='6' required></div></div>
      </section>
      <section class='setup-card'><div class='step-no'>3</div><div class='setup-card-title'><h3>Notificaciones por correo <span class='optional'>Opcional</span></h3><p>Solo salida: el sistema envía avisos, nunca recibe correos.</p></div>
        <label class='switchline'><input type='checkbox' name='notifications_enabled' data-toggle-target='#smtp-fields'><span>Habilitar notificaciones</span></label>
        <div id='smtp-fields' class='form-grid cols3 muted-group'><div><label>Servidor SMTP</label><input name='smtp_host' placeholder='smtp.office365.com'></div><div><label>Puerto</label><input type='number' name='smtp_port' value='587'></div><div><label>Seguridad</label><select name='smtp_security'><option>STARTTLS</option><option>SSL</option><option>NONE</option></select></div><div><label>Cuenta / usuario</label><input name='smtp_user' placeholder='notificaciones@empresa.com'></div><div><label>Clave / App Password</label><input type='password' name='smtp_password'></div><div><label>Remitente</label><input name='smtp_from' placeholder='notificaciones@empresa.com'></div><div class='span3'><label>Destinatarios</label><input name='notification_recipients' placeholder='finanzas@empresa.com, contabilidad@empresa.com'><small>Separe varios correos con coma.</small></div></div>
      </section>
      <section class='setup-card'><div class='step-no'>4</div><div class='setup-card-title'><h3>Conexión SAP Service Layer predeterminada</h3><p>Se usa por defecto; cada base puede sobrescribirla si vive en otro servidor.</p></div>
        <div class='form-grid cols3'><div class='span2'><label>URL raíz Service Layer *</label><input name='service_layer_root' placeholder='https://servidor:50000/b1s' required></div><div><label>OData *</label><select name='odata_version'><option value='v2'>v2</option><option value='v1'>v1</option></select></div><div><label>Versión SAP B1</label><input name='sap_b1_version' value='10.0' placeholder='10.0'></div><div class='span2 endpoint-preview'><span>Endpoint esperado</span><code data-endpoint-preview>https://servidor:50000/b1s/v2</code></div></div>
      </section>
      <section class='setup-card'><div class='step-no'>5</div><div class='setup-card-title with-action'><div><h3>Bases SAP / Multiempresa</h3><p>Agrega una o varias bases. Cada fila puede usar otro Service Layer.</p></div><button type='button' class='btn gold' data-add-company>+ Agregar base</button></div>
        <label class='switchline'><input type='checkbox' name='same_sap_credentials' checked data-same-sap><span>Usar el mismo usuario SAP para todas las bases</span></label>
        <div class='shared-sap-creds' data-shared-creds><div><label>Usuario SAP común</label><input name='shared_sap_user' placeholder='manager / usuario integración'></div><div><label>Contraseña SAP común</label><input type='password' name='shared_sap_password'></div></div>
        <div class='company-builder' data-company-list>
          <div class='company-row' data-company-row><div class='row-index'>1</div><div><label>Nombre empresa/base</label><input name='company_name' placeholder='Empresa Producción' required></div><div><label>Tipo BD</label><select name='db_type'><option>HANA</option><option value='SQLSERVER'>SQL Server</option></select></div><div><label>CompanyDB</label><input name='database_name' placeholder='SBODEMO_PROD' required></div><div><label>Ambiente</label><select name='environment'><option value='TEST'>TEST</option><option value='PROD'>PROD</option></select></div><div><label>Service Layer propio</label><input name='company_service_root' placeholder='Vacío = predeterminado'></div><div><label>OData propio</label><select name='company_odata'><option value=''>Predeterminado</option><option>v2</option><option>v1</option></select></div><div class='individual-creds'><label>Usuario SAP</label><input name='sap_user' placeholder='usuario'></div><div class='individual-creds'><label>Contraseña SAP</label><input type='password' name='sap_password'></div><button class='row-delete' type='button' data-remove-company title='Eliminar'>×</button></div>
        </div>
        <template id='company-row-template'><div class='company-row' data-company-row><div class='row-index'>#</div><div><label>Nombre empresa/base</label><input name='company_name' placeholder='Otra empresa' required></div><div><label>Tipo BD</label><select name='db_type'><option>HANA</option><option value='SQLSERVER'>SQL Server</option></select></div><div><label>CompanyDB</label><input name='database_name' required></div><div><label>Ambiente</label><select name='environment'><option value='TEST'>TEST</option><option value='PROD'>PROD</option></select></div><div><label>Service Layer propio</label><input name='company_service_root' placeholder='Vacío = predeterminado'></div><div><label>OData propio</label><select name='company_odata'><option value=''>Predeterminado</option><option>v2</option><option>v1</option></select></div><div class='individual-creds'><label>Usuario SAP</label><input name='sap_user'></div><div class='individual-creds'><label>Contraseña SAP</label><input type='password' name='sap_password'></div><button class='row-delete' type='button' data-remove-company>×</button></div></template>
      </section>
      <section class='setup-card'><div class='step-no'>6</div><div class='setup-card-title'><h3>Fuentes bancarias / mercado</h3><p>Agrega al menos 3 bancos o fuentes. Pueden ser páginas web, APIs JSON o conectores preconfigurados.</p></div>
        <div class='source-builder' data-source-list>
          <div class='source-row'><div><label>Código *</label><input name='source_code' value='BANPAIS' required></div><div><label>Nombre *</label><input name='source_name' value='Banpaís' required></div><div><label>País</label><input name='source_country' value='Honduras'></div><div><label>Tipo</label><select name='source_type'><option value='PRESET'>Conector conocido</option><option value='WEB_HTML'>Página web</option><option value='API_JSON'>API JSON</option></select></div><div class='span2'><label>URL</label><input name='source_url' value='https://www.banpais.hn/divisas/barradolar.php'></div><div class='span2'><label>Configuración JSON</label><textarea name='source_config'>{{"preset":"BANPAIS"}}</textarea></div><div class='span2'><label>Headers secretos API</label><input type='password' name='source_secret_headers' placeholder='Opcional · JSON cifrado'></div></div>
          <div class='source-row'><div><label>Código *</label><input name='source_code' value='FICOHSA' required></div><div><label>Nombre *</label><input name='source_name' value='Ficohsa' required></div><div><label>País</label><input name='source_country' value='Honduras'></div><div><label>Tipo</label><select name='source_type'><option value='PRESET'>Conector conocido</option><option value='WEB_HTML'>Página web</option><option value='API_JSON'>API JSON</option></select></div><div class='span2'><label>URL</label><input name='source_url' value='https://www.ficohsa.hn/'></div><div class='span2'><label>Configuración JSON</label><textarea name='source_config'>{{"preset":"FICOHSA"}}</textarea></div><div class='span2'><label>Headers secretos API</label><input type='password' name='source_secret_headers' placeholder='Opcional · JSON cifrado'></div></div>
          <div class='source-row'><div><label>Código *</label><input name='source_code' placeholder='BANCO3' required></div><div><label>Nombre *</label><input name='source_name' placeholder='Banco de control' required></div><div><label>País</label><input name='source_country' placeholder='País'></div><div><label>Tipo</label><select name='source_type'><option value='WEB_HTML'>Página web</option><option value='API_JSON'>API JSON</option><option value='PRESET'>Conector conocido</option></select></div><div class='span2'><label>URL *</label><input name='source_url' placeholder='https://banco.example/tasas' required></div><div class='span2'><label>Configuración JSON</label><textarea name='source_config' placeholder='{{"mode":"AUTO","currencies":["USD","EUR"]}}'>{{"mode":"AUTO","currencies":["USD","EUR"]}}</textarea></div><div class='span2'><label>Headers secretos API</label><input type='password' name='source_secret_headers' placeholder='Opcional · JSON cifrado'></div></div>
        </div>
        <p class='muted'>WEB_HTML en modo AUTO intenta detectar compra/venta por moneda. API_JSON puede usar AUTO o rutas JSON explícitas. Después podrás escanear, probar, editar y agregar más fuentes desde Bancos.</p>
      </section>
      <section class='setup-card'><div class='step-no'>7</div><div class='setup-card-title'><h3>Automatización diaria</h3><p>El sistema revisará cada base activa una vez al día y sólo escribirá si las 3 fuentes mínimas son válidas.</p></div>
        <div class='form-grid cols4'><div><label>Hora</label><input type='time' name='schedule_time' value='06:00'></div><div><label>Zona horaria</label><input name='timezone' value='America/Tegucigalpa' placeholder='America/Guatemala'></div><div><label>Monedas</label><input name='currencies_csv' value='USD,EUR' placeholder='USD,EUR'></div><div><label>Fuente oficial</label><input name='primary_bank' value='BANPAIS' placeholder='Código de fuente'></div></div>
        <label class='switchline danger'><input type='checkbox' name='enable_prod_writes'><span>Permitir escritura automática en bases marcadas PROD</span></label>
        <div class='flow-preview'><div><i>⌂</i><b>3+ fuentes</b><span>Trayendo tasas</span></div><em>→</em><div><i>✓</i><b>Consenso</b><span>Mediana y outliers</span></div><em>→</em><div><i>☁</i><b>SAP</b><span>Leyendo tasa actual</span></div><em>→</em><div><i>≠</i><b>Comparación</b><span>Fuente oficial vs consenso</span></div><em>→</em><div><i>✎</i><b>Escritura</b><span>Solo si es segura</span></div><em>→</em><div><i>✓</i><b>Listo</b><span>Verificado y auditado</span></div></div>
      </section>
      <section class='setup-card finish-card'><div class='step-no'>8</div><div class='setup-card-title'><h3>Finalizar configuración</h3><p>Al guardar entrarás al dashboard y comenzará el recorrido guiado.</p></div><button class='btn primary xl' type='submit'>Guardar y entrar a Atas →</button></section>
    </form>
  </main>
</div>"""
    return layout('Configuración inicial',body,setup=True)

@app.get('/setup',response_class=HTMLResponse)
def setup_get():
    if _setup_complete(): return RedirectResponse('/login',303)
    return HTMLResponse(_setup_page())

@app.post('/setup')
async def setup_post(req:Request, logo:UploadFile|None=File(default=None)):
    if _setup_complete(): return RedirectResponse('/login',303)
    try:
        form=await req.form()
        org=str(form.get('organization_name','')).strip()
        admin_user=str(form.get('admin_user','')).strip(); admin_password=str(form.get('admin_password',''))
        root=str(form.get('service_layer_root','')).strip().rstrip('/'); odata=str(form.get('odata_version','v2')).strip().lower(); sap_ver=str(form.get('sap_b1_version','10.0')).strip()
        if not org or not admin_user or len(admin_password)<6: raise ValueError('Complete empresa, usuario y una contraseña de al menos 6 caracteres.')
        if not root.startswith(('http://','https://')) or '/b1s' not in root: raise ValueError('URL de Service Layer inválida. Debe incluir /b1s.')
        root=re.sub(r'/v\d+$','',root,flags=re.I)
        logo_url=_save_logo(logo)
        h=password_hash(admin_password); _set_env_value('WEB_ADMIN_USER',admin_user); _set_env_value('WEB_ADMIN_PASSWORD_HASH',h)
        if not settings.web_session_secret:
            sec=secrets.token_urlsafe(48); _set_env_value('WEB_SESSION_SECRET',sec); settings.web_session_secret=sec
        settings.web_admin_user=admin_user; settings.web_admin_password_hash=h
        notification_enabled='notifications_enabled' in form
        smtp_secret=''
        if notification_enabled and str(form.get('smtp_password','')): smtp_secret=encrypt_secret(str(form.get('smtp_password')))
        logo_setting=logo_url or ''
        store.set_settings({'organization_name':org,'organization_logo':logo_setting,'service_layer_root':root,'odata_version':odata,'sap_b1_version':sap_ver,'sap_base_url':_endpoint(root,odata),'setup_complete':'false','prod_automation_enabled':'true' if 'enable_prod_writes' in form else 'false','notifications_enabled':'true' if notification_enabled else 'false','smtp_host':str(form.get('smtp_host','')).strip(),'smtp_port':str(form.get('smtp_port','587')).strip(),'smtp_security':str(form.get('smtp_security','STARTTLS')).strip(),'smtp_user':str(form.get('smtp_user','')).strip(),'smtp_from':str(form.get('smtp_from','')).strip(),'smtp_secret':smtp_secret,'notification_recipients':str(form.get('notification_recipients','')).strip()})

        # Validate at least three independent market sources before enabling automation.
        scodes=form.getlist('source_code'); snames=form.getlist('source_name'); scountries=form.getlist('source_country'); stypes=form.getlist('source_type'); surls=form.getlist('source_url'); sconfigs=form.getlist('source_config'); ssecrets=form.getlist('source_secret_headers')
        temp_sources=[]; valid_sources=[]; source_errors=[]
        for i,code in enumerate(scodes):
            src={'code':str(code).strip().upper(),'name':str(snames[i] if i<len(snames) else code).strip(),'country':str(scountries[i] if i<len(scountries) else '').strip(),'source_type':str(stypes[i] if i<len(stypes) else 'WEB_HTML').strip().upper(),'url':str(surls[i] if i<len(surls) else '').strip(),'config_json':str(sconfigs[i] if i<len(sconfigs) else '{}').strip() or '{}','headers_json':'{}','timeout_seconds':15,'tls_verify':1}
            secret=str(ssecrets[i] if i<len(ssecrets) else '').strip()
            if secret:
                import json as _json; _json.loads(secret); src['secret_headers_blob']=encrypt_secret(secret)
            if not src['code'] or not src['name']: continue
            temp_sources.append(src)
            try:
                fetch_source(src,settings); valid_sources.append(src['code'])
            except Exception as exc:
                source_errors.append(f"{src['code']}: {exc}")
        if len(valid_sources)<3:
            raise ValueError('Se requieren al menos 3 fuentes bancarias válidas. '+(' | '.join(source_errors) if source_errors else 'Configure y pruebe tres fuentes.'))
        for src in temp_sources:
            sid=store.upsert_bank_source(source_id=None,code=src['code'],name=src['name'],country=src['country'],source_type=src['source_type'],url=src['url'],enabled=True,config_json=src['config_json'],headers_json='{}',timeout_seconds=15,tls_verify=True)
            if src.get('secret_headers_blob'): store.set_bank_source_secret_headers(sid,src['secret_headers_blob'])
            store.mark_bank_source_result(sid,src['code'] in valid_sources,'OK' if src['code'] in valid_sources else next((x for x in source_errors if x.startswith(src['code']+':')),'ERROR'))

        names=form.getlist('company_name'); dbs=form.getlist('database_name'); types=form.getlist('db_type'); envs=form.getlist('environment'); roots=form.getlist('company_service_root'); ods=form.getlist('company_odata'); users=form.getlist('sap_user'); passwords=form.getlist('sap_password')
        if not names: raise ValueError('Agregue al menos una base SAP.')
        same='same_sap_credentials' in form; shared_user=str(form.get('shared_sap_user','')).strip(); shared_pwd=str(form.get('shared_sap_password',''))
        sched=str(form.get('schedule_time','06:00')); hh,mm=(int(x) for x in sched.split(':',1)); currencies_csv=str(form.get('currencies_csv','USD,EUR')).upper().replace(' ','')
        timezone=str(form.get('timezone','America/Tegucigalpa')).strip()
        ZoneInfo(timezone)
        _set_env_value('TIMEZONE',timezone); settings.timezone=timezone; store.timezone=timezone
        store.set_settings({'timezone':timezone})
        use_usd='USD' in currencies_csv.split(','); use_eur='EUR' in currencies_csv.split(',')
        primary=str(form.get('primary_bank',valid_sources[0])).strip().upper()
        if primary not in valid_sources: primary=valid_sources[0]
        secondary=next((x for x in valid_sources if x!=primary),valid_sources[1])
        all_sources=','.join(valid_sources)
        for i,name in enumerate(names):
            user=shared_user if same else (users[i] if i<len(users) else '')
            pwd=shared_pwd if same else (passwords[i] if i<len(passwords) else '')
            if not user or not pwd: raise ValueError(f'Falta usuario/contraseña SAP para {name or dbs[i]}')
            env=(envs[i] if i<len(envs) else 'TEST').upper()
            cid=store.upsert_company(company_id=None,company_name=name,database_name=dbs[i],db_type=types[i] if i<len(types) else 'HANA',environment=env,enabled=True,allow_write=env=='TEST',scheduled_write=True,auto_enabled=True,schedule_hour=hh,schedule_minute=mm,use_usd=use_usd,use_eur=use_eur,sap_user=user,primary_bank=primary,secondary_bank=secondary,service_layer_root=roots[i] if i<len(roots) else '',odata_version=ods[i] if i<len(ods) else '',sap_b1_version=sap_ver,bank_source_codes=all_sources,currencies_csv=currencies_csv)
            store.set_secret_blob(cid,encrypt_secret(pwd))
        store.set_settings({'setup_complete':'true'})
        r=RedirectResponse('/?welcome=1',303); r.set_cookie(COOKIE,sign_session(admin_user,settings.web_session_secret),httponly=True,samesite='strict',secure=False,max_age=28800); return r
    except Exception as exc:
        log.exception('Initial setup failed')
        return HTMLResponse(_setup_page(str(exc)),400)

# ---------------------------------------------------------------------------
# Login/session
# ---------------------------------------------------------------------------
@app.get('/login',response_class=HTMLResponse)
def login_page():
    if not _setup_complete(): return RedirectResponse('/setup',303)
    org=_org(); logo=_logo_url(); brand=f"<img class='login-org-logo' src='{esc(logo)}'>" if logo else "<div class='brand-mark xl'>FX</div>"
    return HTMLResponse(f"""<!doctype html><html lang='es' data-theme='dark'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Atas · Acceso</title><link rel='stylesheet' href='/static/styles.css'><script src='/static/app.js' defer></script></head><body><div class='login-v5'><section class='login-visual'>{brand}<div><div class='eyebrow'>SAP BUSINESS ONE · DAILY FX</div><h1>Control de tasas simple, visual y trazable.</h1><p>{esc(org)}</p></div><div class='login-flow'><span>Banco</span><i>→</i><span>Validación</span><i>→</i><span>SAP</span><i>→</i><span>Auditoría</span></div></section><section class='login-form-wrap'><form method='post' class='login-card v5'><div class='eyebrow'>ACCESO LOCAL</div><h2>Bienvenido</h2><p class='muted'>Ingresa para administrar tasas y automatizaciones.</p><label>Usuario</label><input name='user' autocomplete='username' required><label>Contraseña</label><input type='password' name='password' autocomplete='current-password' required><button class='btn primary xl'>Ingresar →</button><small>Panel local · secretos cifrados por el sistema operativo</small></form></section></div></body></html>""")

@app.post('/login')
async def login(req:Request):
    if not _setup_complete(): return RedirectResponse('/setup',303)
    f=await req.form(); user=str(f.get('user','')); pwd=str(f.get('password',''))
    if user!=settings.web_admin_user or not verify_password(pwd,settings.web_admin_password_hash): return HTMLResponse('Credenciales inválidas',401)
    r=RedirectResponse('/',303); r.set_cookie(COOKIE,sign_session(user,settings.web_session_secret),httponly=True,samesite='strict',secure=False,max_age=28800); return r
@app.get('/logout')
def logout(): r=RedirectResponse('/login',303); r.delete_cookie(COOKIE); return r

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get('/',response_class=HTMLResponse)
def home(req:Request):
    if not _setup_complete(): return RedirectResponse('/setup',303)
    if not _authed(req): return _redirect_login()
    companies=store.list_companies(); active=[x for x in companies if x['enabled']]; tx=store.list_transactions(8); sources=store.list_bank_sources(enabled_only=True); cfg=_cfg()
    now=datetime.now(ZoneInfo(settings.timezone)); today=now.date().isoformat(); summary=store.transaction_summary(today)
    latest_ok=next((x for x in tx if x['status']!='ERROR'),None); latest_err=next((x for x in tx if x['status']=='ERROR'),None)
    next_runs=[]
    for c in active:
        if c.get('auto_enabled'): next_runs.append(f"<div class='mini-run'><span>{esc(c['company_name'])}</span><b>{int(c['schedule_hour']):02d}:{int(c['schedule_minute']):02d}</b><small>{'USD ' if c['use_usd'] else ''}{'EUR' if c['use_eur'] else ''}</small></div>")
    rows=''.join(f"<tr><td>{esc(x['occurred_at'][:19].replace('T',' '))}</td><td>{esc(x['company_db'])}</td><td>{esc(x['currency'])}</td><td>{esc(x['sap_before'] or '—')}</td><td>{esc(x['bank_rate'] or '—')}</td><td>{badge(x['status'])}</td></tr>" for x in tx) or "<tr><td colspan='6' class='empty'>Aún no hay transacciones.</td></tr>"
    bank_status='En línea' if sources and all((x.get('last_status') in {None,'OK'}) for x in sources) else ('Sin fuentes' if not sources else 'Revisar')
    body=f"""
<div class='welcome-strip'><div><div class='eyebrow'>PLATAFORMA CONTABLE</div><h1>Control de Tasas SAP</h1><p>Monitorea, compara y sincroniza la tasa diaria con bancos y SAP Business One.</p></div><form method='post' action='/automation/run-all' data-process='Ejecutando actualización de tasas' data-process-detail='Trayendo datos bancarios, validando, conectando con SAP y verificando resultados.'><button class='btn primary xl'>▶ Ejecutar reconciliación</button></form></div>
<div class='kpi-grid'><a class='kpi-card' href='/companies'><i>▣</i><div><span>Bases SAP</span><b>{len(active)}</b><small>configuradas y activas</small></div></a><a class='kpi-card' href='/banks'><i>⌂</i><div><span>Fuentes</span><b>{len(sources)}</b><small>{bank_status}</small></div></a><a class='kpi-card' href='/automation'><i>⚙</i><div><span>Automatización</span><b>{sum(1 for c in active if c.get('auto_enabled'))}</b><small>programaciones activas</small></div></a><a class='kpi-card' href='/transactions'><i>▤</i><div><span>Transacciones hoy</span><b>{summary.get('total',0)}</b><small>{summary.get('ERROR',0)} errores</small></div></a></div>
<div class='dashboard-grid'><section class='card fx-today'><div class='section-title'><div><h2>Estado contable del día</h2><p>Resumen de la última actividad registrada.</p></div>{badge('OPERATIVO' if not latest_err else 'REVISAR')}</div><div class='sync-ring'><div class='ring'><span>✓</span></div><div><h3>{'Todo alineado' if not latest_err else 'Requiere atención'}</h3><p>{'El sistema está listo para la próxima ejecución.' if not latest_err else esc(latest_err.get('error') or 'Hay errores recientes.')}</p></div></div><div class='mini-stats'><div><span>Última ejecución</span><b>{esc((latest_ok or {}).get('occurred_at','—')[:16].replace('T',' '))}</b></div><div><span>Registros hoy</span><b>{summary.get('total',0)}</b></div><div><span>Errores</span><b>{summary.get('ERROR',0)}</b></div></div></section><section class='card schedule-overview'><div class='section-title'><h2>Próximas ejecuciones</h2><a href='/automation'>Configurar →</a></div>{''.join(next_runs) or '<div class="empty">No hay automatizaciones activas.</div>'}</section></div>
<section class='card'><div class='section-title'><div><h2>Transacciones recientes</h2><p>Lecturas, actualizaciones y verificaciones de SAP.</p></div><a href='/transactions'>Ver todas →</a></div><div class='table-wrap'><table><thead><tr><th>Fecha</th><th>Base</th><th>Moneda</th><th>SAP</th><th>Banco</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table></div></section>
"""
    return HTMLResponse(_ui('Inicio',body))

# ---------------------------------------------------------------------------
# Companies / credentials / SAP test
# ---------------------------------------------------------------------------
def _company_form(c:dict|None=None)->str:
    c=c or {}; cfg=_cfg(); sources=store.list_bank_sources(enabled_only=True)
    env=c.get('environment','TEST'); dbt=c.get('db_type','HANA'); od=c.get('odata_version','')
    selected=set(x.strip().upper() for x in str(c.get('bank_source_codes') or '').split(',') if x.strip())
    if not selected: selected=set(x['code'].upper() for x in sources[:3])
    source_checks=''.join(f"<label><input type='checkbox' name='bank_sources' value='{esc(x['code'])}' {'checked' if x['code'].upper() in selected else ''}> {esc(x['name'])} <small>{esc(x['country'])}</small></label>" for x in sources) or "<span class='muted'>Primero configure al menos 3 fuentes en Bancos.</span>"
    primary_opts=''.join(f"<option value='{esc(x['code'])}' {'selected' if x['code'].upper()==str(c.get('primary_bank') or '').upper() else ''}>{esc(x['name'])}</option>" for x in sources)
    currencies=esc(c.get('currencies_csv') or ('USD,EUR' if c.get('use_eur',1) else 'USD'))
    return f"""<form class='card company-editor' method='post' action='/companies/save' data-process='Guardando base SAP'><input type='hidden' name='company_id' value='{c.get('id','')}'><div class='section-title'><h2>{'Editar base' if c else 'Agregar base SAP'}</h2><span class='pill'>Multiempresa</span></div><div class='form-grid cols3'><div><label>Nombre empresa/base</label><input name='company_name' value='{esc(c.get('company_name',''))}' required></div><div><label>Tipo de BD</label><select name='db_type'><option {'selected' if dbt=='HANA' else ''}>HANA</option><option value='SQLSERVER' {'selected' if dbt=='SQLSERVER' else ''}>SQL Server</option></select></div><div><label>CompanyDB</label><input name='database_name' value='{esc(c.get('database_name',''))}' required></div><div><label>Ambiente</label><select name='environment'><option value='TEST' {'selected' if env=='TEST' else ''}>TEST</option><option value='PROD' {'selected' if env=='PROD' else ''}>PROD</option></select></div><div><label>Usuario SAP</label><input name='sap_user' value='{esc(c.get('sap_user',''))}' required></div><div><label>Contraseña SAP</label><input type='password' name='sap_password' placeholder='Dejar vacío para conservar'></div><div class='span2'><label>Service Layer propio <span class='optional'>opcional</span></label><input name='service_layer_root' value='{esc(c.get('service_layer_root',''))}' placeholder='{esc(cfg.get('service_layer_root',''))}'></div><div><label>OData propio</label><select name='odata_version'><option value='' {'selected' if not od else ''}>Predeterminado</option><option value='v2' {'selected' if od=='v2' else ''}>v2</option><option value='v1' {'selected' if od=='v1' else ''}>v1</option></select></div><div><label>Fuente oficial</label><select name='primary_bank' required>{primary_opts}</select></div><div><label>Monedas</label><input name='currencies_csv' value='{currencies}' placeholder='USD,EUR' required></div><div><label>Hora diaria</label><input type='time' name='schedule_time' value='{int(c.get('schedule_hour',6)):02d}:{int(c.get('schedule_minute',0)):02d}'></div></div><div class='source-selector'><div class='section-title'><div><h3>Fuentes de comparación</h3><p>Mínimo 3 fuentes activas; la fuente oficial debe estar incluida.</p></div><a href='/banks' class='btn secondary'>Administrar fuentes</a></div><div class='check-pills wide'>{source_checks}</div></div><div class='check-pills wide'><label><input type='checkbox' name='enabled' {'checked' if c.get('enabled',1) else ''}> Base activa</label><label><input type='checkbox' name='auto_enabled' {'checked' if c.get('auto_enabled',1 if not c else 0) else ''}> Automatización diaria</label><label><input type='checkbox' name='allow_write' {'checked' if c.get('allow_write',env=='TEST') else ''}> Escritura manual TEST</label><label><input type='checkbox' name='scheduled_write' {'checked' if c.get('scheduled_write',0) else ''}> Autorizar escritura automática</label></div><div class='endpoint-preview'><span>Endpoint efectivo</span><code>{esc(_effective_company_endpoint(c) if c else _endpoint(cfg.get('service_layer_root',''),cfg.get('odata_version','v2')))}</code></div><button class='btn primary'>Guardar base</button></form>"""

@app.get('/companies',response_class=HTMLResponse)
def companies_page(req:Request, edit:int|None=None):
    if not _authed(req): return _redirect_login()
    rows=store.list_companies(); cards=''
    for c in rows:
        cred='Configurada' if c.get('sap_secret') else 'Falta clave'; ep=_effective_company_endpoint(c)
        cards+=f"<article class='company-card'><div class='company-card-head'><div><span class='env-tag {c['environment'].lower()}'>{c['environment']}</span><h3>{esc(c['company_name'])}</h3><code>{esc(c['database_name'])}</code></div>{badge(c.get('last_run_status') or 'SIN EJECUCIÓN')}</div><div class='company-meta'><span>BD <b>{esc(c.get('db_type'))}</b></span><span>Usuario <b>{esc(c.get('sap_user'))}</b></span><span>Credencial <b>{cred}</b></span><span>Hora <b>{int(c['schedule_hour']):02d}:{int(c['schedule_minute']):02d}</b></span></div><div class='endpoint-line' title='{esc(ep)}'>{esc(ep)}</div><div class='company-actions'><a class='btn secondary' href='/companies?edit={c['id']}'>Editar</a><a class='btn secondary' href='/companies/{c['id']}/test'>Probar SAP</a><form method='post' action='/companies/{c['id']}/delete' onsubmit='return confirm(&quot;¿Eliminar esta base?&quot;)'><button class='btn danger'>Eliminar</button></form></div></article>"
    editing=store.get_company(edit) if edit else None
    body=page_header('Bases SAP','Administra CompanyDB, credenciales, Service Layer por empresa y programación.',"<a class='btn primary' href='/companies#editor'>+ Agregar base</a>")+f"<div class='company-grid'>{cards or '<div class="card empty">No hay bases configuradas.</div>'}</div><div id='editor'>{_company_form(editing)}</div>"
    return HTMLResponse(_ui('Bases SAP',body))

@app.post('/companies/save')
async def company_save(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); cid=int(f.get('company_id')) if str(f.get('company_id','')).isdigit() else None; t=str(f.get('schedule_time','06:00')); hh,mm=(int(x) for x in t.split(':',1)); env=str(f.get('environment','TEST')).upper()
    try:
        selected=[str(x).upper() for x in f.getlist('bank_sources') if str(x).strip()]
        if len(selected)<3: raise ValueError('Seleccione al menos 3 fuentes bancarias para comparación.')
        primary=str(f.get('primary_bank','')).upper().strip()
        if primary not in selected: raise ValueError('La fuente oficial debe estar incluida entre las fuentes de comparación.')
        secondary=next((x for x in selected if x!=primary),selected[1])
        currencies_csv=str(f.get('currencies_csv','USD,EUR')).upper().replace(' ','')
        use_usd='USD' in currencies_csv.split(','); use_eur='EUR' in currencies_csv.split(',')
        new_id=store.upsert_company(company_id=cid,company_name=str(f.get('company_name','')),database_name=str(f.get('database_name','')),db_type=str(f.get('db_type','HANA')),environment=env,enabled='enabled' in f,allow_write='allow_write' in f,scheduled_write='scheduled_write' in f,auto_enabled='auto_enabled' in f,schedule_hour=hh,schedule_minute=mm,use_usd=use_usd,use_eur=use_eur,sap_user=str(f.get('sap_user','')),primary_bank=primary,secondary_bank=secondary,service_layer_root=str(f.get('service_layer_root','')),odata_version=str(f.get('odata_version','')),sap_b1_version=_cfg().get('sap_b1_version','10.0'),bank_source_codes=','.join(selected),currencies_csv=currencies_csv)
        pwd=str(f.get('sap_password',''))
        if pwd: store.set_secret_blob(new_id,encrypt_secret(pwd))
    except Exception as exc: return HTMLResponse(_ui('Error',f"<div class='card error-panel'><h2>No se pudo guardar</h2><p>{esc(exc)}</p><a class='btn' href='/companies'>Volver</a></div>"),400)
    return RedirectResponse('/companies',303)

@app.post('/companies/{company_id}/delete')
def company_delete(company_id:int,req:Request):
    if not _authed(req): return _redirect_login()
    store.delete_company(company_id); return RedirectResponse('/companies',303)

@app.get('/companies/{company_id}/test',response_class=HTMLResponse)
def company_test(company_id:int,req:Request):
    if not _authed(req): return _redirect_login()
    c=store.get_company(company_id)
    if not c: return HTMLResponse('No encontrada',404)
    result=inspect_company(settings,store,company_id)
    if result.get('error'): return HTMLResponse(_ui('Prueba SAP',page_header('Prueba SAP',c['company_name'])+f"<div class='card error-panel'><h2>No se pudo completar</h2><p>{esc(result['error'])}</p><a class='btn' href='/companies'>Volver</a></div>"))
    ratecards=''
    for cur,data in result.get('rates',{}).items():
        can_write=data.get('can_test_write') or data.get('can_prod_write'); action=''
        if can_write and not data.get('matches'):
            action=f"<form method='post' action='/companies/{company_id}/write/{cur}' data-process='Aplicando tasa {cur} en SAP' data-process-detail='Validando banco, escribiendo en SAP y verificando la lectura posterior.'><button class='btn primary'>Aplicar tasa bancaria ahora</button></form>"
        ratecards+=f"<div class='rate-card'><div class='section-title'><h2>{cur}</h2>{badge('COINCIDE' if data['matches'] else 'SIN TASA' if data['missing'] else 'DIFERENCIA')}</div><div class='rate-values'><div><span>SAP hoy</span><b>{esc(data['sap'])}</b></div><div><span>Banco oficial</span><b>{esc(data['bank'])}</b></div></div><p>{'La tasa ya coincide.' if data['matches'] else 'Se sugiere la tasa del banco oficial.'}</p>{action}</div>"
    gate='PRODUCCIÓN HABILITADA' if any(d.get('can_prod_write') for d in result.get('rates',{}).values()) else ('PRODUCCIÓN · SOLO LECTURA' if c['environment']=='PROD' else 'BASE DE PRUEBA')
    body=page_header('Prueba SAP',f"{c['company_name']} · {c['database_name']}","<a class='btn secondary' href='/companies'>Volver</a>")+f"<div class='callout info'><b>{gate}</b> · Endpoint: {esc(_effective_company_endpoint(c))}</div><div class='rate-grid'>{ratecards}</div>"
    return HTMLResponse(_ui('Prueba SAP',body))

@app.post('/companies/{company_id}/write/{currency}')
def company_write(company_id:int,currency:str,req:Request):
    if not _authed(req): return _redirect_login()
    try: write_suggested_manual(settings,store,company_id,currency)
    except Exception as exc: return HTMLResponse(_ui('Error',f"<div class='card error-panel'><h2>Error de escritura</h2><p>{esc(exc)}</p></div>"),400)
    return RedirectResponse(f'/companies/{company_id}/test',303)

# ---------------------------------------------------------------------------
# Automation / banks / transactions / reports
# ---------------------------------------------------------------------------
@app.get('/automation',response_class=HTMLResponse)
def automation(req:Request):
    if not _authed(req): return _redirect_login()
    cfg=_cfg(); prod=cfg.get('prod_automation_enabled','false').lower()=='true'; cards=''
    for c in store.list_companies(True):
        cards+=f"<article class='automation-card'><div><span class='env-tag {c['environment'].lower()}'>{c['environment']}</span><h3>{esc(c['company_name'])}</h3><code>{esc(c['database_name'])}</code></div><div class='automation-time'><span>Diario</span><b>{int(c['schedule_hour']):02d}:{int(c['schedule_minute']):02d}</b><small>{'USD ' if c['use_usd'] else ''}{'EUR' if c['use_eur'] else ''}</small></div><div class='automation-status'><span>Última ejecución</span><b>{esc((c.get('last_run_at') or '—')[:19].replace('T',' '))}</b>{badge(c.get('last_run_status') or 'PENDIENTE')}</div><form method='post' action='/automation/run/{c['id']}' data-process='Ejecutando {esc(c['company_name'])}' data-process-detail='Banco → validación → SAP → comparación → escritura → verificación → auditoría.'><button class='btn primary'>▶ Ejecutar ahora</button></form></article>"
    body=page_header('Automatización','Una ejecución diaria por base, con auditoría y verificación.')+f"<div class='prod-control card'><div><div class='eyebrow'>ESCRITURA PRODUCTIVA</div><h2>{'PROD habilitado' if prod else 'PROD bloqueado'}</h2><p>{'Las bases PROD autorizadas pueden escribir.' if prod else 'Las bases PROD permanecen en lectura.'}</p></div><form method='post' action='/automation/prod-toggle'><input type='hidden' name='enabled' value='{'false' if prod else 'true'}'><button class='btn {'danger' if prod else 'primary'}'>{'Bloquear PROD' if prod else 'Habilitar PROD'}</button></form></div><div class='automation-list'>{cards or '<div class="card empty">No hay bases activas.</div>'}</div>"
    return HTMLResponse(_ui('Automatización',body))

@app.post('/automation/prod-toggle')
async def prod_toggle(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); store.set_settings({'prod_automation_enabled':'true' if str(f.get('enabled'))=='true' else 'false'}); return RedirectResponse('/automation',303)

@app.post('/automation/run/{company_id}')
def run_one(company_id:int,req:Request):
    if not _authed(req): return _redirect_login()
    result=reconcile_company(settings,store,company_id,scheduled=True); c=store.get_company(company_id); status='ERROR' if result.get('error') else 'OK'; msg=str(result.get('error') or ', '.join(v.get('status','') for v in result.get('rates',{}).values())); store.mark_run_result(company_id,datetime.now(ZoneInfo(settings.timezone)).date().isoformat(),status,msg); send_run_summary(store,[result]); return RedirectResponse('/automation',303)

@app.post('/automation/run-all')
def run_all(req:Request):
    if not _authed(req): return _redirect_login()
    results=[]; today=datetime.now(ZoneInfo(settings.timezone)).date().isoformat()
    for c in store.list_companies(True):
        if not c.get('auto_enabled'): continue
        r=reconcile_company(settings,store,c['id'],scheduled=True); results.append(r); status='ERROR' if r.get('error') else 'OK'; msg=str(r.get('error') or ', '.join(v.get('status','') for v in r.get('rates',{}).values())); store.mark_run_result(c['id'],today,status,msg)
    send_run_summary(store,results); return RedirectResponse('/',303)

@app.get('/banks',response_class=HTMLResponse)
def banks(req:Request, edit:int|None=None):
    if not _authed(req): return _redirect_login()
    sources=store.list_bank_sources(); editing=store.get_bank_source(edit) if edit else None
    cards=''
    for src in sources:
        status=src.get('last_status') or 'SIN PROBAR'
        cards+=f"""<article class='bank-card source-card'><div class='bank-icon'>{'API' if src['source_type']=='API_JSON' else 'WEB' if src['source_type']=='WEB_HTML' else 'FX'}</div><div class='source-card-main'><div class='section-title'><div><h3>{esc(src['name'])}</h3><small>{esc(src['code'])} · {esc(src['country'] or 'Sin país')} · {esc(src['source_type'])}</small></div>{badge(status)}</div><p>{esc(src['url'] or 'Conector preconfigurado')}</p>{f"<small class='error-text'>{esc(src.get('last_error') or '')}</small>" if src.get('last_error') else ''}<div class='company-actions'><a class='btn secondary' href='/banks?edit={src['id']}#source-editor'>Editar</a><form method='post' action='/banks/{src['id']}/test' data-process='Probando fuente {esc(src['code'])}'><button class='btn secondary'>Probar / escanear</button></form><form method='post' action='/banks/{src['id']}/delete' onsubmit='return confirm(&quot;¿Eliminar esta fuente?&quot;)'><button class='btn danger'>Eliminar</button></form></div></div></article>"""
    e=editing or {}; st=e.get('source_type','WEB_HTML'); cfg=e.get('config_json') or '{{"mode":"AUTO","currencies":["USD","EUR"]}}'
    editor=f"""<form id='source-editor' class='card source-editor' method='post' action='/banks/save' data-process='Guardando fuente bancaria'><input type='hidden' name='source_id' value='{e.get('id','')}'><div class='section-title'><div><h2>{'Editar fuente' if editing else 'Agregar banco / fuente'}</h2><p>Conecta una API JSON o una página web pública. El botón Probar valida la extracción antes de usarla en SAP.</p></div><span class='pill'>Mínimo 3 por base</span></div><div class='form-grid cols3'><div><label>Código</label><input name='code' value='{esc(e.get('code',''))}' placeholder='BANCO_X' required></div><div><label>Nombre</label><input name='name' value='{esc(e.get('name',''))}' placeholder='Banco / Fuente' required></div><div><label>País</label><input name='country' value='{esc(e.get('country',''))}' placeholder='Honduras, Guatemala...'></div><div><label>Tipo</label><select name='source_type'><option value='WEB_HTML' {'selected' if st=='WEB_HTML' else ''}>Página web HTML</option><option value='API_JSON' {'selected' if st=='API_JSON' else ''}>API JSON</option><option value='PRESET' {'selected' if st=='PRESET' else ''}>Conector conocido</option></select></div><div class='span2'><label>URL</label><input name='url' value='{esc(e.get('url',''))}' placeholder='https://banco.example/tasas'></div><div class='span3'><label>Configuración JSON</label><textarea name='config_json' rows='8'>{esc(cfg)}</textarea><small>WEB_HTML/API en AUTO detecta monedas y compra/venta. Para precisión avanzada use CSS, REGEX o mapping JSON.</small></div><div class='span3'><label>Headers HTTP JSON no sensibles <span class='optional'>opcional</span></label><textarea name='headers_json' rows='3'>{esc(e.get('headers_json') or '{}')}</textarea></div><div class='span2'><label>Headers secretos / API key JSON <span class='optional'>opcional · cifrado DPAPI</span></label><input type='password' name='secret_headers_json' placeholder='JSON con Authorization/API-Key · vacío conserva'></div><div><label>Timeout (seg)</label><input type='number' name='timeout_seconds' min='3' max='60' value='{e.get('timeout_seconds',15)}'></div></div><div class='check-pills wide'><label><input type='checkbox' name='enabled' {'checked' if e.get('enabled',1) else ''}> Fuente activa</label><label><input type='checkbox' name='tls_verify' {'checked' if e.get('tls_verify',1) else ''}> Validar TLS</label></div><div class='actions'><button class='btn primary'>Guardar fuente</button><button class='btn secondary' formaction='/banks/preview' formmethod='post' data-process='Escaneando fuente bancaria'>Escanear sin guardar</button></div></form>"""
    guide="""<section class='card source-help'><div class='section-title'><div><h2>Cómo funciona el motor de bancos</h2><p>La empresa puede usar fuentes de cualquier país.</p></div></div><div class='mini-stats'><div><span>1</span><b>Conectar</b><small>API JSON o URL pública</small></div><div><span>2</span><b>Extraer</b><small>AUTO, CSS, Regex o JSON paths</small></div><div><span>3+</span><b>Comparar</b><small>Mediana, desviación y outliers</small></div><div><span>✓</span><b>Aplicar</b><small>La fuente oficial gana sólo si pasa consenso</small></div></div></section>"""
    body=page_header('Bancos y fuentes','Conecta, escanea y valida fuentes de cambio de cualquier país.',"<form method='post' action='/banks/test-all' data-process='Probando todas las fuentes'><button class='btn primary'>Probar todas</button></form>")+guide+f"<div class='bank-grid'>{cards or '<div class="card empty">No hay fuentes. Agregue al menos tres.</div>'}</div>"+editor
    return HTMLResponse(_ui('Bancos',body))

@app.post('/banks/save')
async def banks_save(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); sid=int(f.get('source_id')) if str(f.get('source_id','')).isdigit() else None
    try:
        source_id=store.upsert_bank_source(source_id=sid,code=str(f.get('code','')),name=str(f.get('name','')),country=str(f.get('country','')),source_type=str(f.get('source_type','WEB_HTML')),url=str(f.get('url','')),enabled='enabled' in f,config_json=str(f.get('config_json','{}')),headers_json=str(f.get('headers_json','{}')),timeout_seconds=int(f.get('timeout_seconds',15)),tls_verify='tls_verify' in f)
        secret_headers=str(f.get('secret_headers_json','')).strip()
        if secret_headers:
            import json as _json; _json.loads(secret_headers); store.set_bank_source_secret_headers(source_id,encrypt_secret(secret_headers))
        src=store.get_bank_source(source_id); fetch_source(src,settings); store.mark_bank_source_result(source_id,True,'OK')
    except Exception as exc:
        if sid: store.mark_bank_source_result(sid,False,str(exc))
        return HTMLResponse(_ui('Error de fuente',f"<div class='card error-panel'><h2>No se pudo validar la fuente</h2><p>{esc(exc)}</p><a class='btn' href='/banks'>Volver</a></div>"),400)
    return RedirectResponse('/banks',303)

@app.post('/banks/preview',response_class=HTMLResponse)
async def banks_preview(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); src={'code':str(f.get('code','PREVIEW')).upper(),'name':str(f.get('name','Vista previa')),'country':str(f.get('country','')),'source_type':str(f.get('source_type','WEB_HTML')),'url':str(f.get('url','')),'config_json':str(f.get('config_json','{}')),'headers_json':str(f.get('headers_json','{}')),'timeout_seconds':int(f.get('timeout_seconds',15)),'tls_verify':1 if 'tls_verify' in f else 0}
    if str(f.get('secret_headers_json','')).strip(): src['secret_headers_blob']=encrypt_secret(str(f.get('secret_headers_json')).strip())
    try:
        data=scan_source(src,settings); rows=''.join(f"<tr><td>{esc(cur)}</td><td>{esc(v.get('buy'))}</td><td>{esc(v.get('sell'))}</td></tr>" for cur,v in data['rates'].items())
        body=page_header('Vista previa de fuente',data['name'],"<a class='btn secondary' href='/banks'>Volver</a>")+f"<div class='card'><p><b>URL:</b> {esc(data['source_url'])}</p><table><thead><tr><th>Moneda</th><th>Compra</th><th>Venta</th></tr></thead><tbody>{rows}</tbody></table><p class='success-text'>Extracción correcta. Puede guardar esta configuración.</p></div>"
        return HTMLResponse(_ui('Vista previa',body))
    except Exception as exc:
        return HTMLResponse(_ui('Vista previa',page_header('Escaneo fallido','La fuente respondió, pero no se pudo extraer una tasa válida.',"<a class='btn secondary' href='/banks'>Volver</a>")+f"<div class='card error-panel'><p>{esc(exc)}</p><p>Si la página usa JavaScript dinámico, busque su endpoint API o use selectores/regex estables.</p></div>"),400)

@app.post('/banks/{source_id}/test')
def banks_test_one(source_id:int,req:Request):
    if not _authed(req): return _redirect_login()
    src=store.get_bank_source(source_id)
    if not src: return HTMLResponse('Fuente no encontrada',404)
    try: fetch_source(src,settings); store.mark_bank_source_result(source_id,True,'OK')
    except Exception as exc: store.mark_bank_source_result(source_id,False,str(exc))
    return RedirectResponse('/banks',303)

@app.post('/banks/test-all')
def banks_test_all(req:Request):
    if not _authed(req): return _redirect_login()
    for src in store.list_bank_sources(enabled_only=True):
        try: fetch_source(src,settings); store.mark_bank_source_result(src['id'],True,'OK')
        except Exception as exc: store.mark_bank_source_result(src['id'],False,str(exc))
    return RedirectResponse('/banks',303)

@app.post('/banks/{source_id}/delete')
def banks_delete(source_id:int,req:Request):
    if not _authed(req): return _redirect_login()
    store.delete_bank_source(source_id); return RedirectResponse('/banks',303)

@app.get('/transactions',response_class=HTMLResponse)
def transactions(req:Request):
    if not _authed(req): return _redirect_login()
    rows=store.list_transactions(500); bodyrows=''.join(f"<tr><td>{esc(x['occurred_at'][:19].replace('T',' '))}</td><td>{esc(x['company_name'] or x['company_db'])}</td><td>{esc(x['currency'])}</td><td>{esc(x['primary_bank'] or '—')}</td><td>{esc(x['sap_before'] or '—')}</td><td>{esc(x['bank_rate'] or '—')}</td><td>{esc(x['sap_after'] or '—')}</td><td>{badge(x['status'])}</td></tr>" for x in rows) or "<tr><td colspan='8' class='empty'>Sin registros.</td></tr>"
    body=page_header('Transacciones','Historial contable y técnico de lecturas/escrituras.')+f"<div class='card table-wrap'><table><thead><tr><th>Fecha</th><th>Empresa/Base</th><th>Moneda</th><th>Banco</th><th>SAP antes</th><th>Tasa banco</th><th>SAP después</th><th>Estado</th></tr></thead><tbody>{bodyrows}</tbody></table></div>"; return HTMLResponse(_ui('Transacciones',body))

@app.get('/reports',response_class=HTMLResponse)
def reports(req:Request):
    if not _authed(req): return _redirect_login()
    tx=store.list_transactions(5000); total=len(tx); ok=sum(1 for x in tx if x['verified']); err=sum(1 for x in tx if x['status']=='ERROR')
    body=page_header('Reportes','Exportables para Contabilidad y auditoría.')+f"<div class='kpi-grid'><div class='kpi-card'><div><span>Registros</span><b>{total}</b></div></div><div class='kpi-card'><div><span>Verificados</span><b>{ok}</b></div></div><div class='kpi-card'><div><span>Errores</span><b>{err}</b></div></div></div><div class='card actions'><a class='btn primary' href='/reports/transactions.csv'>Descargar transacciones CSV</a><a class='btn secondary' href='/reports/errors.csv'>Descargar fallos CSV</a></div>"; return HTMLResponse(_ui('Reportes',body))

def _csv(rows,name):
    buf=io.StringIO(newline='');
    if rows: w=csv.DictWriter(buf,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return StreamingResponse(iter([buf.getvalue()]),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename={name}'})
@app.get('/reports/transactions.csv')
def report_tx(req:Request):
    if not _authed(req): return _redirect_login()
    return _csv(store.list_transactions(5000),'sap_fx_transacciones.csv')
@app.get('/reports/errors.csv')
def report_err(req:Request):
    if not _authed(req): return _redirect_login()
    return _csv(store.list_transactions(5000,status='ERROR'),'sap_fx_errores.csv')


# ---------------------------------------------------------------------------
# Reusable settings / branding / notifications
# ---------------------------------------------------------------------------
@app.get('/settings',response_class=HTMLResponse)
def settings_page(req:Request):
    if not _authed(req): return _redirect_login()
    c=_cfg(); notif=c.get('notifications_enabled','false').lower()=='true'; logo=_logo_url(); recipients=c.get('notification_recipients','')
    body=page_header('Configuración','Identidad, integración SAP y notificaciones del producto.')+f"""
<div class='settings-grid'><form class='card' method='post' action='/settings/general' enctype='multipart/form-data' data-process='Guardando configuración general'><div class='section-title'><h2>Empresa e integración predeterminada</h2><span class='pill'>Reutilizable</span></div><div class='brand-config compact'><label class='logo-drop'>{f'<img src="{esc(logo)}">' if logo else '<span>▧</span>'}<b>Cambiar logo</b><input type='file' name='logo' accept='.png,.jpg,.jpeg,.webp'></label><div><label>Nombre empresa</label><input name='organization_name' value='{esc(c.get('organization_name',''))}' required><label>Service Layer raíz</label><input name='service_layer_root' value='{esc(c.get('service_layer_root',''))}' required><div class='form-grid cols2'><div><label>OData</label><select name='odata_version'><option {'selected' if c.get('odata_version')=='v2' else ''}>v2</option><option {'selected' if c.get('odata_version')=='v1' else ''}>v1</option></select></div><div><label>Versión SAP B1</label><input name='sap_b1_version' value='{esc(c.get('sap_b1_version','10.0'))}'></div><div><label>Zona horaria</label><input name='timezone' value='{esc(c.get('timezone',settings.timezone))}' placeholder='America/Tegucigalpa'></div></div></div></div><button class='btn primary'>Guardar</button></form>
<form class='card' method='post' action='/settings/notifications' data-process='Guardando notificaciones'><div class='section-title'><h2>Notificaciones de salida</h2>{badge('ACTIVAS' if notif else 'OPCIONALES')}</div><label class='switchline'><input type='checkbox' name='notifications_enabled' {'checked' if notif else ''}> Habilitar correo saliente</label><div class='form-grid cols2'><div><label>SMTP</label><input name='smtp_host' value='{esc(c.get('smtp_host',''))}'></div><div><label>Puerto</label><input name='smtp_port' value='{esc(c.get('smtp_port','587'))}'></div><div><label>Seguridad</label><select name='smtp_security'><option {'selected' if c.get('smtp_security')=='STARTTLS' else ''}>STARTTLS</option><option {'selected' if c.get('smtp_security')=='SSL' else ''}>SSL</option><option {'selected' if c.get('smtp_security')=='NONE' else ''}>NONE</option></select></div><div><label>Usuario / cuenta</label><input name='smtp_user' value='{esc(c.get('smtp_user',''))}'></div><div><label>Remitente</label><input name='smtp_from' value='{esc(c.get('smtp_from',''))}'></div><div><label>Nueva clave/App Password</label><input type='password' name='smtp_password' placeholder='Vacío = conservar'></div><div class='span2'><label>Destinatarios</label><input name='notification_recipients' value='{esc(recipients)}'></div></div><div class='actions'><button class='btn primary'>Guardar correo</button><button class='btn secondary' formaction='/settings/notifications/test'>Enviar prueba</button></div></form><form class='card' method='post' action='/settings/admin' data-process='Actualizando administrador web'><div class='section-title'><h2>Administrador web</h2><span class='pill'>Local</span></div><p class='muted'>Cambia el usuario y contraseña usados para entrar al panel.</p><div class='form-grid cols2'><div><label>Usuario actual</label><input value='{esc(settings.web_admin_user)}' disabled></div><div><label>Contraseña actual</label><input type='password' name='current_password' required></div><div><label>Nuevo usuario</label><input name='new_user' value='{esc(settings.web_admin_user)}' required></div><div><label>Nueva contraseña</label><input type='password' name='new_password' minlength='6' required></div></div><button class='btn primary'>Actualizar administrador</button></form></div>"""
    return HTMLResponse(_ui('Configuración',body))

@app.post('/settings/general')
async def settings_general(req:Request, logo:UploadFile|None=File(default=None)):
    if not _authed(req): return _redirect_login()
    f=await req.form(); root=re.sub(r'/v\d+$','',str(f.get('service_layer_root','')).strip().rstrip('/'),flags=re.I); od=str(f.get('odata_version','v2')).lower(); tz=str(f.get('timezone',settings.timezone)).strip(); ZoneInfo(tz); vals={'organization_name':str(f.get('organization_name','')).strip(),'service_layer_root':root,'odata_version':od,'sap_b1_version':str(f.get('sap_b1_version','')).strip(),'sap_base_url':_endpoint(root,od),'timezone':tz}; _set_env_value('TIMEZONE',tz); settings.timezone=tz; store.timezone=tz
    if logo and logo.filename: vals['organization_logo']=_save_logo(logo)
    store.set_settings(vals); return RedirectResponse('/settings',303)

async def _save_notification_form(form):
    vals={'notifications_enabled':'true' if 'notifications_enabled' in form else 'false','smtp_host':str(form.get('smtp_host','')).strip(),'smtp_port':str(form.get('smtp_port','587')).strip(),'smtp_security':str(form.get('smtp_security','STARTTLS')).strip(),'smtp_user':str(form.get('smtp_user','')).strip(),'smtp_from':str(form.get('smtp_from','')).strip(),'notification_recipients':str(form.get('notification_recipients','')).strip()}
    pwd=str(form.get('smtp_password',''))
    if pwd: vals['smtp_secret']=encrypt_secret(pwd)
    store.set_settings(vals)

@app.post('/settings/notifications')
async def settings_notifications(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); await _save_notification_form(f); return RedirectResponse('/settings',303)

@app.post('/settings/notifications/test',response_class=HTMLResponse)
async def settings_notifications_test(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); await _save_notification_form(f)
    try: result=send_email(store,'Prueba Atas',f'Notificación de prueba enviada correctamente desde {_org()}.')
    except Exception as exc: return HTMLResponse(_ui('Notificaciones',f"<div class='card error-panel'><h2>No se pudo enviar</h2><p>{esc(exc)}</p><a class='btn' href='/settings'>Volver</a></div>"),400)
    return HTMLResponse(_ui('Notificaciones',f"<div class='card success-panel'><h2>Correo enviado</h2><p>Destinatarios: {result.get('recipients',0)}</p><a class='btn primary' href='/settings'>Volver</a></div>"))

@app.post('/settings/admin')
async def settings_admin(req:Request):
    if not _authed(req): return _redirect_login()
    f=await req.form(); current=str(f.get('current_password','')); new_user=str(f.get('new_user','')).strip(); new_pwd=str(f.get('new_password',''))
    if not verify_password(current,settings.web_admin_password_hash): return HTMLResponse(_ui('Configuración',"<div class='card error-panel'><h2>Contraseña actual incorrecta</h2><a class='btn' href='/settings'>Volver</a></div>"),400)
    if not new_user or len(new_pwd)<6: return HTMLResponse('Datos inválidos',400)
    h=password_hash(new_pwd); _set_env_value('WEB_ADMIN_USER',new_user); _set_env_value('WEB_ADMIN_PASSWORD_HASH',h); settings.web_admin_user=new_user; settings.web_admin_password_hash=h
    r=RedirectResponse('/login',303); r.delete_cookie(COOKIE); return r

@app.get('/logs',response_class=HTMLResponse)
def logs(req:Request):
    if not _authed(req): return _redirect_login()
    p=settings.log_path/'sap_fx_service.log'; text='Sin log todavía.'
    if p.exists(): text=''.join(p.read_text(encoding='utf-8',errors='replace').splitlines(True)[-600:])
    return HTMLResponse(_ui('Logs',page_header('Logs técnicos','Últimas 600 líneas.')+f"<div class='card'><pre>{esc(text)}</pre></div>"))

@app.get('/health')
def health(): return {'status':'ok','service':'Atas','version':get_version(),'setup_complete':_setup_complete(),'enabled_companies':len(store.list_companies(True)),'local_only':True}
