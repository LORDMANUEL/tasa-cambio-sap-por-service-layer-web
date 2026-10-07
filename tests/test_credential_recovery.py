import sqlite3
import zipfile
from pathlib import Path

from app.backup_manager import create_backup
from app.config import Settings
from app.credential_store import encrypt_secret
from app.restore_manager import credential_recovery_report, restore_support_files
from app.store import Store


def test_credential_recovery_report_validates_all_secret_locations(tmp_path):
    db=tmp_path/'credentials.db'
    st=Store(db)
    cid=st.upsert_company(
        company_id=None,company_name='Demo',database_name='DEMO',db_type='HANA',
        environment='TEST',enabled=True,allow_write=True,scheduled_write=False,
        auto_enabled=False,schedule_hour=6,schedule_minute=0,use_usd=True,use_eur=False,
        sap_user='manager',primary_bank='BANPAIS',secondary_bank='FICOHSA',
        bank_source_codes='BANPAIS,FICOHSA,BCH',currencies_csv='USD',
    )
    st.set_secret_blob(cid,encrypt_secret('sap-pass'))
    sid=st.upsert_bank_source(
        source_id=None,code='API',name='API',country='HN',source_type='API_JSON',
        url='https://example.com',enabled=True,config_json='{}',headers_json='{}',
        timeout_seconds=10,tls_verify=True,
    )
    st.set_bank_source_secret_headers(sid,encrypt_secret('{"Authorization":"Bearer demo"}'))
    st.set_settings({'smtp_secret':encrypt_secret('smtp-pass')})

    report=credential_recovery_report(db)
    assert report['checked']==3
    assert report['all_decryptable'] is True
    assert report['reentry_required']==[]


def test_credential_recovery_report_marks_invalid_blob_for_reentry(tmp_path):
    db=tmp_path/'credentials.db'
    st=Store(db)
    cid=st.upsert_company(
        company_id=None,company_name='Demo',database_name='DEMO',db_type='HANA',
        environment='TEST',enabled=True,allow_write=True,scheduled_write=False,
        auto_enabled=False,schedule_hour=6,schedule_minute=0,use_usd=True,use_eur=False,
        sap_user='manager',primary_bank='BANPAIS',secondary_bank='FICOHSA',
        bank_source_codes='BANPAIS,FICOHSA,BCH',currencies_csv='USD',
    )
    with st.conn() as con:
        con.execute("UPDATE companies SET sap_secret='fernet:not-valid' WHERE id=?",(cid,))

    report=credential_recovery_report(db)
    assert report['all_decryptable'] is False
    assert report['reentry_required']==['company:DEMO:sap']


def test_restore_support_files_restores_environment_to_explicit_target(tmp_path):
    db=tmp_path/'live.db'
    Store(db)
    settings=Settings(database_file=str(db))
    backup=create_backup(settings,db,backup_dir=tmp_path/'backups')
    archive=Path(backup['path'])
    rewritten=tmp_path/'with-env.zip'
    with zipfile.ZipFile(archive,'r') as src, zipfile.ZipFile(rewritten,'w') as dst:
        for name in src.namelist():
            dst.writestr(name,src.read(name))
        dst.writestr('app.env',b'TIMEZONE=America/Tegucigalpa\n')

    env_target=tmp_path/'restored.env'
    result=restore_support_files(
        rewritten,
        restore_environment=True,
        environment_target=env_target,
    )
    assert env_target.read_text()=='TIMEZONE=America/Tegucigalpa\n'
    assert str(env_target) in result['restored_support_files']
