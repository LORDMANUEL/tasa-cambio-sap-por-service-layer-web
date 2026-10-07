from pathlib import Path
import importlib.util


def _load():
    path=Path(__file__).resolve().parents[1]/'scripts'/'security'/'scan_secrets.py'
    spec=importlib.util.spec_from_file_location('atas_secret_scan',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_secret_scanner_detects_high_confidence_tokens():
    m=_load()
    token='ghp_' + 'Z'*32
    findings=m._scan_text('app/x.py',f"TOKEN='{token}'")
    assert any(x.rule=='github-token' for x in findings)


def test_secret_scanner_detects_literal_credentials_outside_tests():
    m=_load()
    findings=m._scan_text('app/config.py',"password='RealPassword123!'")
    assert any(x.rule=='literal-secret-assignment' for x in findings)


def test_secret_scanner_allows_test_fixture_credentials():
    m=_load()
    findings=m._scan_text('tests/test_auth.py',"password='admin123'")
    assert not any(x.rule=='literal-secret-assignment' for x in findings)
