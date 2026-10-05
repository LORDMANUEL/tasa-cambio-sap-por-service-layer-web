"""SAP/bank orchestration for SAP FX Control Center V5.

Three flows are intentionally separate:
1. inspect_company(): read-only diagnostic used by the web "Probar" button.
2. write_suggested_test(): explicit TEST-only write used after a diagnostic.
3. reconcile_company(... scheduled=True): automatic daily policy execution.
"""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
import logging
from zoneinfo import ZoneInfo
from app.config import Settings
from app.store import Store
from app.credential_store import decrypt_secret, CredentialError
from app.sap_client import SapCompany, SapFxClient, SapError
from app.market_sources import build_consensus
from app.policy import decide_rate_action

log=logging.getLogger(__name__)


def _sap_url(settings:Settings, store:Store, row:dict) -> str:
    """Resolve the effective Service Layer endpoint for one company.

    Company-specific root/OData overrides support multi-company towers where each
    SAP tenant exposes a different Service Layer. Empty overrides fall back to the
    installation-wide endpoint configured in the setup wizard.
    """
    runtime=store.get_settings()
    root=(row.get('service_layer_root') or runtime.get('service_layer_root') or '').strip().rstrip('/')
    version=(row.get('odata_version') or runtime.get('odata_version') or 'v2').strip().lower()
    if root:
        import re
        root=re.sub(r'/v\d+$','',root,flags=re.I)
        return f"{root}/{version}"
    return runtime.get('sap_base_url',settings.sap_base_url).rstrip('/')


def _currencies(row:dict) -> list[str]:
    csv=str(row.get('currencies_csv') or '').strip()
    if csv:
        out=list(dict.fromkeys(x.strip().upper() for x in csv.split(',') if x.strip()))
        if out: return out
    out=[]
    if row.get('use_usd',1): out.append('USD')
    if row.get('use_eur',1): out.append('EUR')
    return out or ['USD']


def _password(row:dict) -> str:
    if not row.get('sap_secret'): raise CredentialError('SAP_PASSWORD_NOT_CONFIGURED')
    return decrypt_secret(row['sap_secret'])


def _comparison(settings:Settings, store:Store, row:dict):
    return build_consensus(store,settings,row,_currencies(row))


def _official_rates(comparison) -> dict[str,Decimal]:
    return dict(comparison.official_rates)


def inspect_company(settings:Settings, store:Store, company_id:int) -> dict:
    """Read SAP + bank rates without writing anything, including PROD."""
    row=store.get_company(company_id)
    if not row: raise ValueError('Compañía no encontrada')
    result={'company':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],'rates':{},'read_only':True}
    try:
        comparison=_comparison(settings,store,row)
        result['warnings']=comparison.warnings; result['bank_safe']=comparison.safe
        result['market_sources']=comparison.successful_sources; result['market_failed']=comparison.failed_sources
        if not comparison.safe:
            result['error']='BANK_VALIDATION_FAILED'; return result
        official=_official_rates(comparison); password=_password(row)
        sap_url=_sap_url(settings,store,row)
        today=datetime.now(ZoneInfo(settings.timezone)).date()
        company=SapCompany(row['database_name'],row['environment'],False)
        with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=settings.sap_verify_tls,timeout=settings.sap_timeout_seconds) as sap:
            result['local_currency']=sap.get_local_currency()
            for cur in _currencies(row):
                before=sap.get_currency_rate(cur,today); bank=official[cur]; decision=decide_rate_action(before,bank)
                result['rates'][cur]={
                    'sap':str(before),'bank':str(bank),'decision':decision.action,
                    'missing':before==0,'matches':decision.action=='MATCH',
                    'can_test_write': row['environment']=='TEST' and bool(row.get('allow_write')) and decision.action!='MATCH',
                    'can_prod_write': row['environment']=='PROD' and store.get_settings().get('prod_automation_enabled','false').lower()=='true' and bool(row.get('scheduled_write')) and decision.action!='MATCH'
                }
                store.add_transaction({
                    'company_id':row['id'],'company_db':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],
                    'currency':cur,'primary_bank':row['primary_bank'],'secondary_bank':row['secondary_bank'],'sap_before':str(before),'bank_rate':str(bank),
                    'sap_after':str(before),'decision':'INSPECT_'+decision.action,'status':'READ_ONLY','verified':1,'details_json':'web-test'
                })
        return result
    except Exception as exc:
        log.exception('Company inspection failed company=%s',row['database_name']); result['error']=str(exc); return result


def write_suggested_test(settings:Settings, store:Store, company_id:int, currency:str) -> dict:
    """Write the current official-bank suggestion to a TEST company and verify it."""
    row=store.get_company(company_id)
    if not row: raise ValueError('Compañía no encontrada')
    cur=currency.upper()
    if row['environment']!='TEST': raise SapError('La prueba de escritura manual sólo está permitida en TEST.')
    if not row.get('allow_write'): raise SapError('Active "Permitir prueba de escritura" en esta base TEST.')
    if cur not in _currencies(row): raise SapError(f'{cur} no está habilitada en esta base.')
    comparison=_comparison(settings,store,row)
    if not comparison.safe: raise SapError('Validación bancaria no segura: '+'; '.join(comparison.warnings))
    bank=_official_rates(comparison)[cur]; password=_password(row)
    sap_url=_sap_url(settings,store,row)
    today=datetime.now(ZoneInfo(settings.timezone)).date(); company=SapCompany(row['database_name'],'TEST',True)
    with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=settings.sap_verify_tls,timeout=settings.sap_timeout_seconds) as sap:
        before=sap.get_currency_rate(cur,today); sap.set_currency_rate(cur,today,bank); after=sap.get_currency_rate(cur,today)
        if after!=bank: raise SapError(f'Verificación fallida: esperado {bank}, leído {after}')
    status='CREATED_VERIFIED' if before==0 else 'UPDATED_VERIFIED'
    store.add_transaction({'company_id':row['id'],'company_db':row['database_name'],'company_name':row['company_name'],'environment':'TEST','currency':cur,'primary_bank':row['primary_bank'],'secondary_bank':row['secondary_bank'],'sap_before':str(before),'bank_rate':str(bank),'sap_after':str(after),'decision':'TEST_WRITE','status':status,'verified':1,'details_json':'manual-test-write'})
    return {'currency':cur,'before':str(before),'bank':str(bank),'after':str(after),'status':status}


def write_suggested_manual(settings:Settings, store:Store, company_id:int, currency:str) -> dict:
    """Apply the official bank rate manually to TEST or explicitly-enabled PROD and verify it."""
    row=store.get_company(company_id)
    if not row: raise ValueError('Compañía no encontrada')
    cur=currency.upper()
    runtime=store.get_settings()
    if row['environment']=='TEST':
        if not row.get('allow_write'):
            raise SapError('Active "Permitir prueba de escritura" en esta base TEST.')
    else:
        if runtime.get('prod_automation_enabled','false').lower()!='true':
            raise SapError('PROD está bloqueado globalmente. Habilítelo en Automatización.')
        if not row.get('scheduled_write'):
            raise SapError('Esta base PROD no tiene autorizada la escritura. Active "Autorizar escritura programada".')
    if cur not in _currencies(row): raise SapError(f'{cur} no está habilitada en esta base.')
    comparison=_comparison(settings,store,row)
    if not comparison.safe: raise SapError('Validación bancaria no segura: '+'; '.join(comparison.warnings))
    bank=_official_rates(comparison)[cur]; password=_password(row)
    sap_url=_sap_url(settings,store,row)
    today=datetime.now(ZoneInfo(settings.timezone)).date(); company=SapCompany(row['database_name'],row['environment'],True)
    with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=settings.sap_verify_tls,timeout=settings.sap_timeout_seconds) as sap:
        before=sap.get_currency_rate(cur,today)
        if before==bank:
            after=before; status='MATCH'
        else:
            sap.set_currency_rate(cur,today,bank); after=sap.get_currency_rate(cur,today)
            if after!=bank: raise SapError(f'Verificación fallida: esperado {bank}, leído {after}')
            status='CREATED_VERIFIED' if before==0 else 'UPDATED_VERIFIED'
    store.add_transaction({'company_id':row['id'],'company_db':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],'currency':cur,'primary_bank':row['primary_bank'],'secondary_bank':row['secondary_bank'],'sap_before':str(before),'bank_rate':str(bank),'sap_after':str(after),'decision':'MANUAL_BANK_WRITE','status':status,'verified':1,'details_json':'manual-bank-write'})
    return {'currency':cur,'before':str(before),'bank':str(bank),'after':str(after),'status':status,'environment':row['environment']}

def _scheduled_write_allowed(store:Store,row:dict) -> bool:
    if not row.get('scheduled_write') or not row.get('auto_enabled'): return False
    if row['environment']=='TEST': return True
    global_ok=store.get_settings().get('prod_automation_enabled','false').lower()=='true'
    return global_ok


def reconcile_company(settings:Settings, store:Store, company_id:int, *, scheduled:bool=True) -> dict:
    """Execute policy reconciliation. Production writes require explicit schedule authorization."""
    row=store.get_company(company_id)
    if not row: raise ValueError('Compañía no encontrada')
    if not row['enabled']: return {'company':row['database_name'],'status':'DISABLED'}
    comparison=_comparison(settings,store,row)
    result={'company':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],'bank_safe':comparison.safe,'warnings':comparison.warnings,'rates':{}}
    if not comparison.safe: return {**result,'error':'BANK_VALIDATION_FAILED'}
    try: password=_password(row)
    except CredentialError as exc: return {**result,'error':str(exc)}
    today=datetime.now(ZoneInfo(settings.timezone)).date(); sap_url=_sap_url(settings,store,row)
    official=_official_rates(comparison); allowed=_scheduled_write_allowed(store,row) if scheduled else (row['environment']=='TEST' and bool(row.get('allow_write')))
    company=SapCompany(row['database_name'],row['environment'],allowed)
    try:
        with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=settings.sap_verify_tls,timeout=settings.sap_timeout_seconds) as sap:
            for cur in _currencies(row):
                before=sap.get_currency_rate(cur,today); bank=official[cur]; decision=decide_rate_action(before,bank)
                tx={'company_id':row['id'],'company_db':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],'currency':cur,'primary_bank':row['primary_bank'],'secondary_bank':row['secondary_bank'],'sap_before':str(before),'bank_rate':str(bank),'decision':decision.action}
                if decision.action=='MATCH':
                    tx.update(sap_after=str(before),status='MATCH',verified=1); result['rates'][cur]={'status':'MATCH','before':str(before),'after':str(before),'bank':str(bank)}
                elif not allowed:
                    status=f'{decision.action}_WRITE_BLOCKED'; tx.update(sap_after=str(before),status=status,verified=0); result['rates'][cur]={'status':status,'before':str(before),'after':str(before),'bank':str(bank)}
                else:
                    sap.set_currency_rate(cur,today,bank); after=sap.get_currency_rate(cur,today)
                    if after!=bank: raise SapError(f'Verificación fallida: esperado {bank}, leído {after}')
                    status='CREATED_VERIFIED' if decision.action=='CREATE' else 'UPDATED_VERIFIED'; tx.update(sap_after=str(after),status=status,verified=1); result['rates'][cur]={'status':status,'before':str(before),'after':str(after),'bank':str(bank)}
                store.add_transaction(tx)
        return result
    except Exception as exc:
        log.exception('SAP reconciliation failed company=%s',row['database_name'])
        result['error']=str(exc)
        record_system_error(store,row,str(exc),'reconcile')
        return result


def _run_status(result:dict) -> tuple[str,str]:
    if result.get('error'):
        return 'ERROR', str(result.get('error'))
    rates=result.get('rates') or {}
    statuses=[str(v.get('status','')) for v in rates.values()]
    if not statuses:
        return 'OK', 'Sin monedas pendientes.'
    if any('VERIFIED' in x or x=='MATCH' for x in statuses):
        return 'OK', ', '.join(statuses)
    if any('BLOCKED' in x for x in statuses):
        return 'BLOCKED', ', '.join(statuses)
    return 'OK', ', '.join(statuses)

def record_system_error(store:Store,row:dict,error:str,source:str='scheduler') -> None:
    store.add_transaction({
        'company_id':row['id'],'company_db':row['database_name'],'company_name':row['company_name'],
        'environment':row['environment'],'currency':'SYSTEM','primary_bank':row.get('primary_bank'),
        'secondary_bank':row.get('secondary_bank'),'sap_before':None,'bank_rate':None,'sap_after':None,
        'decision':source.upper(),'status':'ERROR','verified':0,'error':str(error),'details_json':source
    })

def run_due_schedules(settings:Settings, store:Store) -> list[dict]:
    """Run each active company at most once per local day after its configured time."""
    now=datetime.now(ZoneInfo(settings.timezone)); today=now.date().isoformat(); out=[]
    for row in store.list_companies(enabled_only=True):
        if not row.get('auto_enabled'): continue
        if row.get('last_run_date')==today: continue
        due=(now.hour,now.minute) >= (int(row.get('schedule_hour') or 0),int(row.get('schedule_minute') or 0))
        if not due: continue
        result=reconcile_company(settings,store,row['id'],scheduled=True)
        status,message=_run_status(result)
        store.mark_run_result(row['id'],today,status,message)
        if result.get('error'):
            record_system_error(store,row,result['error'],'scheduler')
        out.append(result)
    return out


def reconcile_all(settings:Settings, store:Store) -> dict:
    rows=store.list_companies(enabled_only=True); out=[reconcile_company(settings,store,row['id'],scheduled=True) for row in rows if row.get('auto_enabled')]
    cfg=store.get_settings(); store.cleanup(int(cfg.get('log_retention_days',settings.log_retention_days)))
    return {'timestamp':store.now(),'companies':out,'count':len(out)}
