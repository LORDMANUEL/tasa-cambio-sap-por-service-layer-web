"""SAP/bank orchestration for Atas V5.

Three flows are intentionally separate:
1. inspect_company(): read-only diagnostic used by the web "Probar" button.
2. write_suggested_test(): explicit TEST-only write used after a diagnostic.
3. reconcile_company(... scheduled=True): automatic daily policy execution.
"""
from __future__ import annotations
from datetime import datetime, timedelta
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


def _require_company(store: Store, company_id: int) -> dict:
    """Return one configured company or fail with the canonical domain error."""
    row = store.get_company(company_id)
    if not row:
        raise ValueError('Compañía no encontrada')
    return row


def _local_day(settings: Settings):
    """Return today's date in the installation timezone."""
    return datetime.now(ZoneInfo(settings.timezone)).date()


def _setting_enabled(value: object) -> bool:
    """Normalize persisted booleans coming from SQLite/string settings."""
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


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


def _sap_verify_tls(settings:Settings, store:Store) -> bool:
    value=store.get_settings().get('sap_verify_tls')
    if value is None:
        return bool(settings.sap_verify_tls)
    return _setting_enabled(value)


def _password(row:dict) -> str:
    if not row.get('sap_secret'): raise CredentialError('SAP_PASSWORD_NOT_CONFIGURED')
    return decrypt_secret(row['sap_secret'])


def _comparison(settings:Settings, store:Store, row:dict):
    return build_consensus(store,settings,row,_currencies(row))


def _official_rates(comparison) -> dict[str,Decimal]:
    return dict(comparison.official_rates)


def inspect_company(settings:Settings, store:Store, company_id:int) -> dict:
    """Read SAP first, then enrich with bank consensus without ever writing."""
    row=_require_company(store, company_id)
    result={
        'company':row['database_name'],
        'company_name':row['company_name'],
        'environment':row['environment'],
        'rates':{},
        'read_only':True,
    }
    try:
        password=_password(row)
        sap_url=_sap_url(settings,store,row)
        today=_local_day(settings)
        currencies=_currencies(row)
        sap_rates={}
        company=SapCompany(row['database_name'],row['environment'],False)
        with SapFxClient(
            sap_url,company,row['sap_user'],password,
            verify_tls=_sap_verify_tls(settings,store),
            timeout=settings.sap_timeout_seconds,
        ) as sap:
            result['local_currency']=sap.get_local_currency()
            for cur in currencies:
                sap_rates[cur]=sap.get_currency_rate(cur,today)

        # Bank problems must never prevent the user from validating SAP read access.
        try:
            comparison=_comparison(settings,store,row)
            result['warnings']=comparison.warnings
            result['notices']=getattr(comparison,'notices',[])
            result['bank_safe']=comparison.safe
            result['market_sources']=comparison.successful_sources
            result['market_failed']=comparison.failed_sources
        except Exception as exc:
            log.exception('Bank comparison failed during SAP inspection company=%s',row['database_name'])
            comparison=None
            result['warnings']=[str(exc)]
            result['notices']=[]
            result['bank_safe']=False
            result['market_sources']=[]
            result['market_failed']={}
        if not result['bank_safe']:
            result['bank_error']='BANK_VALIDATION_FAILED'

        official=_official_rates(comparison) if comparison and comparison.safe else {}
        for cur in currencies:
            before=sap_rates[cur]
            bank=official.get(cur)
            if bank is None:
                decision_action='BANK_BLOCKED'
                matches=False
                can_test=False
                can_prod=False
            else:
                decision=decide_rate_action(before,bank)
                decision_action=decision.action
                matches=decision.action=='MATCH'
                can_test=row['environment']=='TEST' and bool(row.get('allow_write')) and not matches
                can_prod=(
                    row['environment']=='PROD'
                    and _setting_enabled(store.get_settings().get('prod_automation_enabled', 'false'))
                    and bool(row.get('scheduled_write'))
                    and not matches
                )
            result['rates'][cur]={
                'sap':str(before),
                'bank':str(bank) if bank is not None else None,
                'decision':decision_action,
                'missing':before==0,
                'matches':matches,
                'can_test_write':can_test,
                'can_prod_write':can_prod,
            }
            store.add_transaction({
                'company_id':row['id'],
                'company_db':row['database_name'],
                'company_name':row['company_name'],
                'environment':row['environment'],
                'currency':cur,
                'primary_bank':row['primary_bank'],
                'secondary_bank':row['secondary_bank'],
                'sap_before':str(before),
                'bank_rate':str(bank) if bank is not None else None,
                'sap_after':str(before),
                'decision':'INSPECT_'+decision_action,
                'status':'READ_ONLY' if bank is not None else 'READ_ONLY_BANK_BLOCKED',
                'verified':1,
                'details_json':'web-test',
            })
        return result
    except Exception as exc:
        log.exception('Company inspection failed company=%s',row['database_name'])
        result['error']=str(exc)
        return result

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
    today=_local_day(settings); company=SapCompany(row['database_name'],'TEST',True)
    with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=_sap_verify_tls(settings,store),timeout=settings.sap_timeout_seconds) as sap:
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
        if not _setting_enabled(runtime.get('prod_automation_enabled', 'false')):
            raise SapError('PROD está bloqueado globalmente. Habilítelo en Automatización.')
        if not row.get('scheduled_write'):
            raise SapError('Esta base PROD no tiene autorizada la escritura. Active "Autorizar escritura programada".')
    if cur not in _currencies(row): raise SapError(f'{cur} no está habilitada en esta base.')
    comparison=_comparison(settings,store,row)
    if not comparison.safe: raise SapError('Validación bancaria no segura: '+'; '.join(comparison.warnings))
    bank=_official_rates(comparison)[cur]; password=_password(row)
    sap_url=_sap_url(settings,store,row)
    today=_local_day(settings); company=SapCompany(row['database_name'],row['environment'],True)
    with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=_sap_verify_tls(settings,store),timeout=settings.sap_timeout_seconds) as sap:
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
    """Automatic scheduler gate: requires automation + explicit write authorization."""
    if not row.get('auto_enabled') or not row.get('scheduled_write'):
        return False
    if row['environment']=='TEST':
        return True
    return _setting_enabled(store.get_settings().get('prod_automation_enabled', 'false'))


def _manual_reconcile_write_allowed(store:Store,row:dict) -> bool:
    """Manual 'run now' gate; independent from whether a daily schedule is enabled."""
    if row['environment']=='TEST':
        return bool(row.get('allow_write') or row.get('scheduled_write'))
    return (
        bool(row.get('scheduled_write'))
        and _setting_enabled(store.get_settings().get('prod_automation_enabled', 'false'))
    )


def reconcile_company(settings:Settings, store:Store, company_id:int, *, scheduled:bool=True) -> dict:
    """Execute policy reconciliation. Production writes require explicit schedule authorization."""
    row=store.get_company(company_id)
    if not row: raise ValueError('Compañía no encontrada')
    if not row['enabled']: return {'company':row['database_name'],'status':'DISABLED'}
    comparison=_comparison(settings,store,row)
    result={'company':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],'bank_safe':comparison.safe,'warnings':comparison.warnings,'notices':getattr(comparison,'notices',[]),'rates':{}}
    if not comparison.safe:
        error='BANK_VALIDATION_FAILED'
        record_system_error(store,row,error,'bank-validation')
        return {**result,'error':error,'error_recorded':True}
    try:
        password=_password(row)
    except CredentialError as exc:
        error=str(exc)
        record_system_error(store,row,error,'credentials')
        return {**result,'error':error,'error_recorded':True}
    today=_local_day(settings); sap_url=_sap_url(settings,store,row)
    official=_official_rates(comparison)
    currencies=_currencies(row)

    waiting={}
    if scheduled:
        for cur in currencies:
            previous=store.previous_market_observation(
                row['primary_bank'],
                cur,
                today.isoformat(),
            )
            if previous is None:
                continue
            previous_sell=Decimal(str(previous['sell']))
            if official[cur] == previous_sell:
                waiting[cur]={
                    'status':'WAITING_BANK_UPDATE',
                    'bank':str(official[cur]),
                    'previous_bank':str(previous_sell),
                    'previous_day':previous['observed_day'],
                }
                store.add_transaction({
                    'company_id':row['id'],
                    'company_db':row['database_name'],
                    'company_name':row['company_name'],
                    'environment':row['environment'],
                    'currency':cur,
                    'primary_bank':row['primary_bank'],
                    'secondary_bank':row['secondary_bank'],
                    'sap_before':None,
                    'bank_rate':str(official[cur]),
                    'sap_after':None,
                    'decision':'WAIT_FOR_BANK_REFRESH',
                    'status':'WAITING_BANK_UPDATE',
                    'verified':0,
                    'details_json':f"same-as-{previous['observed_day']}",
                })
        result['rates'].update(waiting)
        if waiting:
            result['retry_required']=True
            result['retry_after_minutes']=60

    active_currencies=[cur for cur in currencies if cur not in waiting]
    if not active_currencies:
        return result

    allowed=_scheduled_write_allowed(store,row) if scheduled else _manual_reconcile_write_allowed(store,row)
    company=SapCompany(row['database_name'],row['environment'],allowed)
    try:
        with SapFxClient(sap_url,company,row['sap_user'],password,verify_tls=_sap_verify_tls(settings,store),timeout=settings.sap_timeout_seconds) as sap:
            for cur in active_currencies:
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
        result['error_recorded']=True
        return result


def _run_status(result:dict) -> tuple[str,str]:
    if result.get('error'):
        return 'ERROR', str(result.get('error'))
    rates=result.get('rates') or {}
    statuses=[str(v.get('status','')) for v in rates.values()]
    if not statuses:
        return 'OK', 'Sin monedas pendientes.'
    if any(x=='WAITING_BANK_UPDATE' for x in statuses):
        return 'WAITING_BANK_UPDATE', ', '.join(statuses)
    if any('BLOCKED' in x for x in statuses):
        return 'BLOCKED', ', '.join(statuses)
    if any('VERIFIED' in x or x=='MATCH' for x in statuses):
        return 'OK', ', '.join(statuses)
    return 'OK', ', '.join(statuses)

def record_system_error(store:Store,row:dict,error:str,source:str='scheduler') -> None:
    store.add_transaction({
        'company_id':row['id'],'company_db':row['database_name'],'company_name':row['company_name'],
        'environment':row['environment'],'currency':'SYSTEM','primary_bank':row.get('primary_bank'),
        'secondary_bank':row.get('secondary_bank'),'sap_before':None,'bank_rate':None,'sap_after':None,
        'decision':source.upper(),'status':'ERROR','verified':0,'error':str(error),'details_json':source
    })

def run_due_schedules(settings:Settings, store:Store) -> list[dict]:
    """Run each active company at most once per local day after its configured time.

    The database claim is atomic. It prevents duplicate automatic executions if
    two scheduler loops overlap or two local server processes start together.
    Manual "run now" actions intentionally remain separate from this daily lock.
    """
    now=datetime.now(ZoneInfo(settings.timezone)); today=now.date().isoformat(); out=[]
    for row in store.list_companies(enabled_only=True):
        if not row.get('auto_enabled'): continue
        if row.get('scheduler_claim_date')==today: continue
        retry_at=row.get('scheduler_next_retry_at')
        if retry_at:
            try:
                if now < datetime.fromisoformat(retry_at):
                    continue
            except ValueError:
                log.warning('Invalid scheduler_next_retry_at company=%s value=%s',row['database_name'],retry_at)
        due=(now.hour,now.minute) >= (int(row.get('schedule_hour') or 0),int(row.get('schedule_minute') or 0))
        if not due: continue
        if not store.claim_daily_run(row['id'],today):
            continue
        try:
            result=reconcile_company(settings,store,row['id'],scheduled=True)
        except Exception as exc:
            log.exception('Unexpected scheduler failure company=%s',row['database_name'])
            result={'company':row['database_name'],'company_name':row['company_name'],'environment':row['environment'],'rates':{},'error':str(exc)}
        status,message=_run_status(result)
        if result.get('retry_required'):
            next_retry=(now+timedelta(hours=1)).isoformat()
            store.schedule_daily_retry(
                row['id'],
                today,
                next_retry,
                f'Tasa bancaria sin cambio respecto al día anterior; reintento {next_retry}',
            )
            result['next_retry_at']=next_retry
        else:
            store.mark_run_result(row['id'],today,status,message)
        if result.get('error') and not result.get('error_recorded'):
            record_system_error(store,row,result['error'],'scheduler')
        out.append(result)
    return out


def reconcile_all(settings:Settings, store:Store) -> dict:
    rows=store.list_companies(enabled_only=True); out=[reconcile_company(settings,store,row['id'],scheduled=True) for row in rows if row.get('auto_enabled')]
    cfg=store.get_settings(); store.cleanup(int(cfg.get('log_retention_days',settings.log_retention_days)))
    return {'timestamp':store.now(),'companies':out,'count':len(out)}
