"""SAP FX Control Center V5 - generic, local-first accounting platform.

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

app=FastAPI(title='SAP FX Control Center V5',version='5.0.0',lifespan=lifespan,docs_url=None)
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
    <div class='setup-product'><div class='brand-mark xl'>FX</div><div><strong>SAP FX</strong><span>Control Center V5</span></div></div>
    <div class='setup-hero-art'><div class='server-stack'><i></i><i></i><i></i><b>SAP</b></div></div>
    <h1>Bienvenido a SAP FX Control Center</h1>
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
