"""Validation helpers for the initial Atas setup."""
from __future__ import annotations


def currency_source_coverage(snapshots: dict[str, object], currencies: list[str]) -> dict[str, list[str]]:
    """Return valid source codes publishing each requested currency."""
    coverage={}
    for currency in [str(c).upper().strip() for c in currencies if str(c).strip()]:
        coverage[currency]=[
            code
            for code,snap in snapshots.items()
            if currency in getattr(snap,"rates",{})
        ]
    return coverage


def require_currency_source_coverage(
    snapshots: dict[str, object],
    currencies: list[str],
    *,
    minimum: int=3,
) -> dict[str, list[str]]:
    """Require enough validated sources for every requested currency."""
    coverage=currency_source_coverage(snapshots,currencies)
    missing={cur:codes for cur,codes in coverage.items() if len(codes)<minimum}
    if missing:
        details="; ".join(
            f"{cur}: {len(codes)} fuente(s) válida(s) [{', '.join(codes) or 'ninguna'}]"
            for cur,codes in missing.items()
        )
        raise ValueError(
            f"Cada moneda seleccionada requiere al menos {minimum} fuentes válidas. {details}"
        )
    return coverage
