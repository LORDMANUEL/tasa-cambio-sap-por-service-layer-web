"""High-volume deterministic regression matrix for Atas critical rules.

These cases intentionally vary financial values and source configurations.  They are
not duplicate smoke tests: each parametrized row exercises the production policy,
pair validation, parser, or setup coverage with a distinct input.
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.market_sources import (
    MarketSourceError,
    SourceSnapshot,
    _extract_html,
    _extract_json,
    validate_snapshot_pairs,
)
from app.policy import decide_rate_action
from app.setup_validation import require_currency_source_coverage


def _rate(i: int) -> Decimal:
    return Decimal("20") + (Decimal(i) / Decimal("100"))


CREATE_CASES=[(_rate(i),) for i in range(90)]
MATCH_CASES=[(_rate(i),) for i in range(90)]
UPDATE_CASES=[(_rate(i), _rate(i)+Decimal("0.37")) for i in range(90)]
INVALID_BANK_CASES=[Decimal("0")-Decimal(i)/Decimal("100") for i in range(20)]


@pytest.mark.parametrize("bank_rate", [x[0] for x in CREATE_CASES])
def test_policy_create_matrix(bank_rate):
    d=decide_rate_action(Decimal("0"),bank_rate)
    assert d.action=="CREATE"
    assert "crear" in d.reason.lower()


@pytest.mark.parametrize("rate", [x[0] for x in MATCH_CASES])
def test_policy_match_matrix(rate):
    d=decide_rate_action(rate,rate)
    assert d.action=="MATCH"
    assert "coincide" in d.reason.lower()


@pytest.mark.parametrize("sap_rate,bank_rate", UPDATE_CASES)
def test_policy_update_matrix(sap_rate,bank_rate):
    d=decide_rate_action(sap_rate,bank_rate)
    assert d.action=="UPDATE"
    assert sap_rate != bank_rate


@pytest.mark.parametrize("bank_rate", INVALID_BANK_CASES)
def test_policy_rejects_nonpositive_bank_matrix(bank_rate):
    with pytest.raises(ValueError,match="mayor que cero"):
        decide_rate_action(Decimal("27.00"),bank_rate)


VALID_PAIR_CASES=[
    (
        Decimal("18") + Decimal(i)/Decimal("100"),
        Decimal("18") + Decimal(i)/Decimal("100") + Decimal("0.10") + Decimal(i%5)/Decimal("100"),
    )
    for i in range(80)
]


@pytest.mark.parametrize("buy,sell", VALID_PAIR_CASES)
def test_pair_validation_accepts_plausible_matrix(buy,sell):
    snap=SourceSnapshot(
        "SRC","Source","WEB_HTML","https://example.test",
        "2026-10-13T06:00:00-06:00",
        {"USD":{"buy":buy,"sell":sell}},
        "hash",
    )
    validate_snapshot_pairs(snap,"35")
    assert sell >= buy


SELL_BELOW_BUY_CASES=[
    (
        Decimal("25") + Decimal(i)/Decimal("100"),
        Decimal("25") + Decimal(i)/Decimal("100") - Decimal("0.01") - Decimal(i%3)/Decimal("100"),
    )
    for i in range(40)
]


@pytest.mark.parametrize("buy,sell", SELL_BELOW_BUY_CASES)
def test_pair_validation_rejects_sell_below_buy_matrix(buy,sell):
    snap=SourceSnapshot(
        "SRC","Source","WEB_HTML","https://example.test",
        "2026-10-13T06:00:00-06:00",
        {"USD":{"buy":buy,"sell":sell}},
        "hash",
    )
    with pytest.raises(MarketSourceError,match="menor que compra"):
        validate_snapshot_pairs(snap,"35")


NONPOSITIVE_PAIR_CASES=[]
for i in range(15):
    NONPOSITIVE_PAIR_CASES.append((Decimal("0")-Decimal(i)/Decimal("100"),Decimal("27")))
    NONPOSITIVE_PAIR_CASES.append((Decimal("27"),Decimal("0")-Decimal(i)/Decimal("100")))


@pytest.mark.parametrize("buy,sell", NONPOSITIVE_PAIR_CASES)
def test_pair_validation_rejects_nonpositive_matrix(buy,sell):
    snap=SourceSnapshot(
        "SRC","Source","WEB_HTML","https://example.test",
        "2026-10-13T06:00:00-06:00",
        {"USD":{"buy":buy,"sell":sell}},
        "hash",
    )
    with pytest.raises(MarketSourceError,match="mayor que cero"):
        validate_snapshot_pairs(snap,"35")


EXCESSIVE_SPREAD_CASES=[
    (
        Decimal("10") + Decimal(i)/Decimal("100"),
        (Decimal("10") + Decimal(i)/Decimal("100")) * Decimal("1.50"),
    )
    for i in range(40)
]


@pytest.mark.parametrize("buy,sell", EXCESSIVE_SPREAD_CASES)
def test_pair_validation_rejects_excessive_spread_matrix(buy,sell):
    snap=SourceSnapshot(
        "SRC","Source","API_JSON","https://example.test",
        "2026-10-13T06:00:00-06:00",
        {"USD":{"buy":buy,"sell":sell}},
        "hash",
    )
    with pytest.raises(MarketSourceError,match="spread compra/venta"):
        validate_snapshot_pairs(snap,"20")


JSON_CASES=[
    (
        f"{Decimal('20') + Decimal(i)/Decimal('100'):.4f}",
        f"{Decimal('20.10') + Decimal(i)/Decimal('100'):.4f}",
    )
    for i in range(50)
]


@pytest.mark.parametrize("buy,sell", JSON_CASES)
def test_json_mapping_regression_matrix(buy,sell):
    data={"fx":{"rows":[{"code":"USD","purchase":buy,"sale":sell}]}}
    config={
        "mode":"MAPPING",
        "currencies":["USD"],
        "mapping":{"USD":{"buy":"fx.rows[0].purchase","sell":"fx.rows[0].sale"}},
    }
    out=_extract_json(data,config)
    assert out["USD"]["buy"]==Decimal(buy)
    assert out["USD"]["sell"]==Decimal(sell)


HTML_CASES=[
    (
        f"{Decimal('21') + Decimal(i)/Decimal('100'):.4f}",
        f"{Decimal('21.12') + Decimal(i)/Decimal('100'):.4f}",
    )
    for i in range(30)
]


@pytest.mark.parametrize("buy,sell", HTML_CASES)
def test_html_regex_regression_matrix(buy,sell):
    html=f"<section><strong>USD</strong> Compra: {buy} Venta: {sell}</section>"
    config={
        "mode":"REGEX",
        "currencies":["USD"],
        "mapping":{"USD":{"regex":r"USD.*?Compra:\\s*(?P<buy>[0-9.]+).*?Venta:\\s*(?P<sell>[0-9.]+)"}},
    }
    out=_extract_html(html,config)
    assert out["USD"]["buy"]==Decimal(buy)
    assert out["USD"]["sell"]==Decimal(sell)


COVERAGE_CASES=[3 + (i % 3) for i in range(30)]


@pytest.mark.parametrize("minimum", COVERAGE_CASES)
def test_setup_source_coverage_matrix(minimum):
    snapshots={
        f"SRC{i}":SimpleNamespace(rates={"USD":{"buy":1,"sell":1}})
        for i in range(minimum)
    }
    coverage=require_currency_source_coverage(snapshots,["USD"],minimum=minimum)
    assert len(coverage["USD"])==minimum
    assert coverage["USD"]==list(snapshots)
