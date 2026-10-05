"""Human-friendly connectivity check for all configured market sources."""
from app.config import get_settings
from app.store import Store
from app.market_sources import fetch_source

def main() -> int:
    settings=get_settings(); store=Store(settings.db_path,settings.timezone); sources=store.list_bank_sources(enabled_only=True)
    print('='*72); print(' PRUEBA DE FUENTES DE CAMBIO - SAP FX CONTROL CENTER V5'); print('='*72)
    if not sources: print(' No hay fuentes configuradas. Abra el panel web -> Bancos.'); return 1
    failures=0
    for src in sources:
        print(f"\n[{src['code']}] {src['name']} · {src['country']} · {src['source_type']}")
        try:
            snap=fetch_source(src,settings); store.mark_bank_source_result(src['id'],True,'OK'); print(' Estado : OK'); print(f" Fuente : {snap.source_url}")
            for cur,pair in snap.rates.items(): print(f" {cur:>4} compra {pair['buy']} | venta {pair['sell']}")
        except Exception as exc:
            failures+=1; store.mark_bank_source_result(src['id'],False,str(exc)); print(' Estado : ERROR'); print(f' Detalle: {exc}')
    ok=len(sources)-failures; print('\n'+'='*72); print(f' RESULTADO: {ok}/{len(sources)} fuentes válidas')
    if ok<3: print(' ADVERTENCIA: se requieren al menos 3 fuentes válidas para automatizar escrituras SAP.')
    return 0 if failures==0 and ok>=3 else 1
if __name__=='__main__': raise SystemExit(main())
