from types import SimpleNamespace

import pytest

from app.setup_validation import currency_source_coverage, require_currency_source_coverage


def _snap(*currencies):
    return SimpleNamespace(rates={cur:{"buy":1,"sell":1} for cur in currencies})


def test_currency_source_coverage_counts_each_currency_independently():
    snapshots={
        "BANPAIS":_snap("USD","EUR"),
        "FICOHSA":_snap("USD","EUR"),
        "BCH":_snap("USD"),
    }
    coverage=currency_source_coverage(snapshots,["USD","EUR"])
    assert coverage["USD"]==["BANPAIS","FICOHSA","BCH"]
    assert coverage["EUR"]==["BANPAIS","FICOHSA"]


def test_setup_coverage_rejects_currency_with_only_two_sources():
    snapshots={
        "BANPAIS":_snap("USD","EUR"),
        "FICOHSA":_snap("USD","EUR"),
        "BCH":_snap("USD"),
    }
    with pytest.raises(ValueError,match="EUR: 2 fuente"):
        require_currency_source_coverage(snapshots,["USD","EUR"],minimum=3)


def test_setup_coverage_accepts_three_sources_per_currency():
    snapshots={
        "A":_snap("USD","EUR"),
        "B":_snap("USD","EUR"),
        "C":_snap("USD","EUR"),
    }
    result=require_currency_source_coverage(snapshots,["USD","EUR"],minimum=3)
    assert result["USD"]==["A","B","C"]
    assert result["EUR"]==["A","B","C"]


def test_wizard_has_individual_steps_and_recovery_hooks():
    from pathlib import Path
    from app.main import _setup_page
    page=_setup_page()
    script=(Path(__file__).resolve().parents[1]/"app"/"static"/"app.js").read_text(encoding="utf-8")
    assert page.count("<section class='setup-card") == 8
    assert "data-setup-next" in script
    assert "sessionStorage.setItem(key" in script
    assert "el.type==='password'" in script
    assert "new FormData(setupForm)" in script
    assert "setError(message)" in script
