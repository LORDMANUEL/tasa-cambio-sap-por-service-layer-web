"""Service-layer helpers used by API flows to retrieve and validate exchange-rate data."""
from __future__ import annotations
import logging
from app.config import Settings
from app.models import BankRates, Comparison
from app.providers import get_provider
log=logging.getLogger(__name__)
def _pct_diff(a,b): return 999.0 if a==0 else abs(a-b)/a*100.0
def validate_range(rates: BankRates, settings: Settings):
    warnings=[]
    for label,value,low,high in [("USD compra",rates.usd.buy,settings.usd_min,settings.usd_max),("USD venta",rates.usd.sell,settings.usd_min,settings.usd_max),("EUR compra",rates.eur.buy,settings.eur_min,settings.eur_max),("EUR venta",rates.eur.sell,settings.eur_min,settings.eur_max)]:
        if not low<=value<=high: warnings.append(f"{rates.bank}: {label}={value} fuera de rango [{low},{high}]")
    if rates.usd.sell<rates.usd.buy: warnings.append(f"{rates.bank}: USD venta menor que compra")
    if rates.eur.sell<rates.eur.buy: warnings.append(f"{rates.bank}: EUR venta menor que compra")
    return warnings

def fetch_pair(settings: Settings, primary_name: str, secondary_name: str|None, store=None) -> Comparison:
    primary=get_provider(primary_name,settings).fetch()
    if store: store.add_bank_check(primary_name,True,primary)
    warnings=validate_range(primary,settings); secondary=None; ud=ed=up=ep=None
    if secondary_name and secondary_name!=primary_name:
        try:
            secondary=get_provider(secondary_name,settings).fetch()
            if store: store.add_bank_check(secondary_name,True,secondary)
            warnings.extend(validate_range(secondary,settings)); ud=abs(primary.usd.sell-secondary.usd.sell); ed=abs(primary.eur.sell-secondary.eur.sell); up=_pct_diff(primary.usd.sell,secondary.usd.sell); ep=_pct_diff(primary.eur.sell,secondary.eur.sell)
            if up>settings.max_bank_spread_percent: warnings.append(f"USD diferencia bancos {up:.3f}% excede límite")
            if ep>settings.max_bank_spread_percent: warnings.append(f"EUR diferencia bancos {ep:.3f}% excede límite")
        except Exception as exc:
            if store: store.add_bank_check(secondary_name,False,error=str(exc))
            warnings.append(f"Proveedor secundario no disponible: {exc}")
    return Comparison(primary=primary,secondary=secondary,usd_sell_diff=ud,eur_sell_diff=ed,usd_sell_diff_percent=up,eur_sell_diff_percent=ep,safe_for_reference=(len(warnings)==0),warnings=warnings)
