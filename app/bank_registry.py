"""Registry of Honduran commercial banks and connector support status.

The catalog follows the CNBS commercial-bank list. Only sources whose public
rate page has been validated for stable automated parsing are marked automatic.
"""
BANKS = {
    "BANPAIS": {"name":"Banco del País, S.A.","automatic":True,"currencies":["USD","EUR"],"status":"FUNCIONA","note":"HTML público directo; conector automático validado.","url":"https://www.banpais.hn/divisas/barradolar.php"},
    "FICOHSA": {"name":"Banco Financiera Comercial Hondureña, S.A.","automatic":True,"currencies":["USD","EUR"],"status":"FUNCIONA","note":"Página pública de tasas; conector automático validado.","url":"https://www.ficohsa.hn/"},
    "ATLANTIDA": {"name":"Banco Atlántida, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Publica tasas, pero la página carga cifras dinámicamente; falta endpoint estable validado.","url":"https://bancatlan.hn/"},
    "OCCIDENTE": {"name":"Banco de Occidente, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "CUSCATLAN": {"name":"Banco Cuscatlán Honduras, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "FICENSA": {"name":"Banco Financiera Centroamericana, S.A. (FICENSA)","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "BANHCAFE": {"name":"Banco Hondureño del Café, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "LAFISE": {"name":"Banco LAFISE Honduras, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin endpoint público estable validado para automatización.","url":""},
    "DAVIVIENDA": {"name":"Banco Davivienda Honduras, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "PROMERICA": {"name":"Banco Promerica, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "BANRURAL": {"name":"Banco de Desarrollo Rural Honduras, S.A. (BANRURAL)","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "AZTECA": {"name":"Banco Azteca de Honduras, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "POPULAR": {"name":"Banco Popular, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "BAC": {"name":"Banco de América Central Honduras, S.A. (BAC)","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Cotiza divisas, pero no se ha validado un endpoint público simple y estable.","url":""},
    "BANCO_HONDURAS": {"name":"Banco de Honduras, S.A.","automatic":False,"currencies":["USD","EUR"],"status":"PENDIENTE","note":"Sin conector público estable validado para V5.","url":""},
    "BCH": {"name":"Banco Central de Honduras","automatic":False,"currencies":["USD"],"status":"REFERENCIA","note":"Referencia oficial/regulatoria; no se usa como precio financiero principal de compra.","url":"https://www.bch.hn/"},
}

def automatic_banks():
    return [k for k,v in BANKS.items() if v["automatic"]]
