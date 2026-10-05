"""Outgoing-only email notifications for Atas V5."""
from __future__ import annotations
import smtplib
import ssl
from email.message import EmailMessage
from app.credential_store import decrypt_secret


class NotificationError(RuntimeError):
    pass


def recipients_from_text(value: str) -> list[str]:
    raw=(value or '').replace(';',',').replace('\n',',')
    return [x.strip() for x in raw.split(',') if x.strip()]


def send_email(store, subject: str, text: str) -> dict:
    cfg=store.get_settings()
    if cfg.get('notifications_enabled','false').lower()!='true':
        return {'sent':False,'reason':'DISABLED'}
    host=cfg.get('smtp_host','').strip()
    try:
        port=int(cfg.get('smtp_port','587') or 587)
    except ValueError as exc:
        raise NotificationError('Puerto SMTP inválido') from exc
    if not 1 <= port <= 65535:
        raise NotificationError('Puerto SMTP fuera de rango')
    mode=cfg.get('smtp_security','STARTTLS').upper()
    if mode not in {'STARTTLS','SSL','NONE'}:
        raise NotificationError('Modo SMTP inválido; use STARTTLS, SSL o NONE')
    user=cfg.get('smtp_user','').strip()
    sender=cfg.get('smtp_from','').strip() or user
    recipients=recipients_from_text(cfg.get('notification_recipients',''))
    secret=cfg.get('smtp_secret','')
    if not host or not sender or not recipients or not secret:
        raise NotificationError('Configuración SMTP incompleta')

    password=decrypt_secret(secret)
    msg=EmailMessage()
    msg['Subject']=subject
    msg['From']=sender
    msg['To']=', '.join(recipients)
    msg.set_content(text)

    if mode=='SSL':
        with smtplib.SMTP_SSL(host,port,timeout=20,context=ssl.create_default_context()) as s:
            if user:
                s.login(user,password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host,port,timeout=20) as s:
            s.ehlo()
            if mode=='STARTTLS':
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            if user:
                s.login(user,password)
            s.send_message(msg)
    return {'sent':True,'recipients':len(recipients)}


def _result_needs_attention(result: dict) -> bool:
    if result.get('error'):
        return True
    for data in (result.get('rates') or {}).values():
        status=str(data.get('status') or '').upper()
        if 'BLOCKED' in status or 'ERROR' in status or 'FAILED' in status:
            return True
    return False


def send_run_summary(store, results: list[dict]) -> None:
    if not results:
        return
    cfg=store.get_settings()
    attention=[r for r in results if _result_needs_attention(r)]
    if attention and cfg.get('notify_errors','true').lower()!='true':
        return
    if not attention and cfg.get('notify_success','true').lower()!='true':
        return

    org=cfg.get('organization_name','Mi Empresa')
    lines=[f'Resumen diario de tasas - {org}','']
    for r in results:
        state=r.get('error') or ('ATENCIÓN' if _result_needs_attention(r) else 'OK')
        lines.append(f"{r.get('company_name') or r.get('company')}: {state}")
        for cur,data in (r.get('rates') or {}).items():
            lines.append(
                f"  {cur}: {data.get('status')} | banco {data.get('bank')} | SAP {data.get('after')}"
            )
    subject_state='ATENCIÓN REQUERIDA' if attention else 'Proceso completado'
    try:
        send_email(store,f"Atas - {subject_state} - {org}",'\n'.join(lines))
    except Exception:
        import logging
        logging.getLogger(__name__).exception('Email notification failed')
