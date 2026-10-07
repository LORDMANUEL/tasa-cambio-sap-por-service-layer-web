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
