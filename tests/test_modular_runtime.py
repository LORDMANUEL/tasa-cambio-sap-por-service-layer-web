from pathlib import Path
from types import SimpleNamespace

from app.runtime_config import effective_company_endpoint, service_layer_endpoint, set_env_value


def test_service_layer_endpoint_normalizes_version():
    assert service_layer_endpoint('https://sap.local:50000/b1s/v1','v2')=='https://sap.local:50000/b1s/v2'
    assert service_layer_endpoint('https://sap.local:50000/b1s/','v1')=='https://sap.local:50000/b1s/v1'


def test_effective_company_endpoint_prefers_company_override():
    cfg={'service_layer_root':'https://global/b1s','odata_version':'v2'}
    company={'service_layer_root':'https://company/b1s','odata_version':'v1'}
    assert effective_company_endpoint(company,cfg)=='https://company/b1s/v1'


def test_set_env_value_preserves_other_keys(tmp_path):
    (tmp_path/'.env').write_text('A=1\nTIMEZONE=Old/Zone\n',encoding='utf-8')
    set_env_value(tmp_path,'TIMEZONE','America/Tegucigalpa')
    text=(tmp_path/'.env').read_text(encoding='utf-8')
    assert 'A=1' in text
    assert 'TIMEZONE=America/Tegucigalpa' in text
    assert 'Old/Zone' not in text


def test_scheduler_service_run_once_isolated(monkeypatch):
    import app.scheduler_runtime as sr

    calls={'summary':0,'cleanup':None}
    store=SimpleNamespace(cleanup=lambda days:calls.update(cleanup=days))
    monkeypatch.setattr(sr,'run_due_schedules',lambda settings,store:[{'company':'DEMO'}])
    service=sr.SchedulerService(
        settings=object(),
        store=store,
        config_getter=lambda:{'log_retention_days':'45'},
        summary_sender=lambda store,results:calls.update(summary=len(results)),
        logger=SimpleNamespace(info=lambda *a,**k:None,exception=lambda *a,**k:None),
    )
    result=service.run_once()
    assert len(result)==1
    assert calls['summary']==1
    assert calls['cleanup']==45
