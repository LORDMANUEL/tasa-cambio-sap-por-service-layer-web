"""Server-rendered UI helpers for Atas V5."""
from __future__ import annotations
import html

def esc(value)->str: return html.escape('' if value is None else str(value))

def badge(value)->str:
    text=esc(value); upper=text.upper()
    css='ok' if any(x in upper for x in ('MATCH','VERIFIED','OK','CREATED','UPDATED','ACTIVA','FUNCIONA','LISTO','EN LÍNEA')) else ('bad' if any(x in upper for x in ('ERROR','FAILED','BLOCKED','FALLÓ')) else 'warn')
    return f"<span class='badge {css}'>{text}</span>"

def page_header(title:str,subtitle:str='',action_html:str='')->str:
    return f"<div class='page-head'><div><div class='eyebrow'>ATAS</div><h1>{esc(title)}</h1><div class='page-subtitle'>{esc(subtitle)}</div></div><div class='actions'>{action_html}</div></div>"

def layout(title:str,body:str, *, organization:str='Mi Empresa', logo_url:str='', setup:bool=False)->str:
    if setup:
        return f"""<!doctype html><html lang='es' data-theme='dark'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta name='color-scheme' content='dark light'><title>{esc(title)} · Atas</title><link rel='stylesheet' href='/static/styles.css'><script src='/static/app.js' defer></script></head><body class='setup-body'>{body}</body></html>"""
    nav=[('/', 'Inicio','⌂'),('/companies','Bases SAP','▣'),('/automation','Automatización','◴'),('/banks','Bancos','⌂'),('/transactions','Transacciones','▤'),('/reports','Reportes','▥'),('/settings','Configuración','⚙'),('/logs','Logs','≡')]
    nav_html=''.join(f"<a class='nav-link' href='{href}'><span class='nav-icon'>{icon}</span><span>{label}</span><span class='nav-chevron'>›</span></a>" for href,label,icon in nav)
    logo = f"<img class='org-logo' src='{esc(logo_url)}' alt='Logo'>" if logo_url else "<div class='brand-mark'>FX</div>"
    return f"""<!doctype html><html lang='es' data-theme='dark'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta name='color-scheme' content='dark light'><title>{esc(title)} · Atas</title><link rel='stylesheet' href='/static/styles.css'><script src='/static/app.js' defer></script></head><body>
<div class='app-shell'>
<aside class='sidebar' id='sidebar'><div class='brand'>{logo}<div class='brand-copy'><b>SAP FX</b><span>Control Center</span></div></div><div class='org-panel'><strong>{esc(organization)}</strong><span>Tasa de cambio diaria</span></div><div class='nav-label'>PLATAFORMA</div>{nav_html}<div class='nav-label'>SESIÓN</div><a class='nav-link logout' href='/logout'><span class='nav-icon'>↪</span><span>Cerrar sesión</span></a><div class='sidebar-foot'><span class='status-dot'></span><div><b>Servicio en línea</b><small>Panel local · 127.0.0.1</small></div></div></aside>
<section class='main-area'><header class='topbar'><button class='icon-btn mobile-menu' type='button' data-menu-toggle aria-label='Menú'>☰</button><div class='search-shell'><span>⌕</span><input placeholder='Buscar en la plataforma...' disabled></div><div class='topbar-actions'><span class='muted live-clock' data-live-clock></span><button class='tour-btn' type='button' data-tour-start>✦ Recorrido</button><button class='theme-toggle' type='button' data-theme-toggle><span data-theme-icon>◐</span><span data-theme-label>Claro</span></button><div class='admin-chip'><span class='avatar'>AD</span><div><b>Administrador</b><small>{esc(organization)}</small></div></div></div></header>
<main>{body}<div class='footer-note'>Atas V5 · Automatización diaria de tasas · SAP Business One</div></main></section></div><div class='sidebar-backdrop' data-sidebar-backdrop></div></body></html>"""
