"""Generic market-source engine for SAP FX Control Center V5.

Supports:
- PRESET: validated built-in connectors (Banpaís/Ficohsa).
- API_JSON: REST/JSON endpoint with configurable dotted paths.
- WEB_HTML: public HTML page with AUTO, CSS or REGEX extraction.

The engine never writes SAP. It only retrieves and normalizes market rates.
The reconciliation layer requires at least three valid sources before a write.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from statistics import median
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from app.config import Settings
from app.providers import get_provider
from app.providers.http_client import secure_session
from app.credential_store import decrypt_secret


class MarketSourceError(RuntimeError):
    pass


@dataclass
class SourceSnapshot:
    code: str
    name: str
    source_type: str
    source_url: str
    fetched_at: str
    rates: dict[str, dict[str, Decimal]]
    raw_hash: str

    def serializable(self) -> dict[str, Any]:
        d = asdict(self)
        d["rates"] = {c: {k: str(v) for k, v in pair.items()} for c, pair in self.rates.items()}
        return d


@dataclass
class MarketConsensus:
    safe: bool
    official_source: str
    official_rates: dict[str, Decimal]
    medians: dict[str, Decimal]
    deviations_percent: dict[str, Decimal]
    successful_sources: list[str]
    failed_sources: dict[str, str]
    warnings: list[str]
    snapshots: list[SourceSnapshot]
    notices: list[str] = field(default_factory=list)


def _safe_url(url: str) -> str:
    url = (url or "").strip()
    p = urlparse(url)
    if p.scheme not in {"http", "https"} or not p.netloc:
        raise MarketSourceError("La fuente debe usar una URL http:// o https:// válida.")
    return url


def _decimal(value: Any) -> Decimal:
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    s = str(value).strip()
    s = re.sub(r"[^0-9,.-]", "", s)
    if not s:
        raise MarketSourceError("No se encontró un número válido.")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        tail = s.split(",")[-1]
        if len(tail) in {2, 3, 4, 5, 6}:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        out = Decimal(s)
    except InvalidOperation as exc:
        raise MarketSourceError(f"Valor numérico inválido: {value}") from exc
    if out <= 0:
        raise MarketSourceError(f"La tasa debe ser mayor que cero: {value}")
    return out


def _json_path(data: Any, path: str) -> Any:
    cur = data
    for token in re.findall(r"[^.\[\]]+|\[\d+\]", path.strip()):
        if token.startswith("["):
            cur = cur[int(token[1:-1])]
        elif isinstance(cur, dict):
            cur = cur[token]
        else:
            raise KeyError(path)
    return cur


def _normalize_config(source: dict) -> dict:
    raw = source.get("config_json") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception as exc:
        raise MarketSourceError("config_json de la fuente no es JSON válido.") from exc


def _headers(source: dict) -> dict[str, str]:
    raw = source.get("headers_json") or "{}"
    try:
        obj = raw if isinstance(raw, dict) else json.loads(raw)
        headers={str(k):str(v) for k,v in obj.items()} if isinstance(obj,dict) else {}
    except Exception:
        headers={}
    secret=source.get("secret_headers_blob")
    if secret:
        try:
            obj=json.loads(decrypt_secret(secret))
            if isinstance(obj,dict): headers.update({str(k):str(v) for k,v in obj.items()})
        except Exception as exc:
            raise MarketSourceError("No se pudieron descifrar los headers secretos de la API.") from exc
    return headers


def _fetch_http(source: dict, settings: Settings) -> requests.Response:
    url = _safe_url(source.get("url", ""))
    session = secure_session()
    try:
        response = session.get(
            url,
            headers=_headers(source),
            timeout=min(max(int(source.get("timeout_seconds") or settings.request_timeout_seconds), 3), 60),
            verify=bool(source.get("tls_verify", 1)),
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MarketSourceError(f"No se pudo consultar la fuente: {exc.__class__.__name__}") from exc
    if len(response.content) > 4_000_000:
        raise MarketSourceError("La respuesta excede 4 MB; no se procesará.")
    return response


def _auto_html(text: str, currency: str) -> dict[str, Decimal]:
    normalized = re.sub(r"\s+", " ", text)
    positions = [m.start() for m in re.finditer(rf"\b{re.escape(currency)}\b", normalized, re.I)]
    aliases = {"USD": ["DOLAR", "DÓLAR", "DOLLAR"], "EUR": ["EURO"]}.get(currency.upper(), [])
    for alias in aliases:
        positions.extend(m.start() for m in re.finditer(re.escape(alias), normalized, re.I))
    for pos in sorted(set(positions))[:20]:
        window = normalized[pos:pos + 500]
        nums = re.findall(r"(?<!\d)(\d{1,6}(?:[.,]\d{2,6})?)(?!\d)", window)
        vals: list[Decimal] = []
        for n in nums:
            try:
                v = _decimal(n)
                if Decimal("0.00001") < v < Decimal("1000000"):
                    vals.append(v)
            except Exception:
                pass
        buy = re.search(r"(?:compra|buy|purchase)\D{0,30}(\d{1,6}(?:[.,]\d{2,6})?)", window, re.I)
        sell = re.search(r"(?:venta|sell|sale)\D{0,30}(\d{1,6}(?:[.,]\d{2,6})?)", window, re.I)
        if buy and sell:
            return {"buy": _decimal(buy.group(1)), "sell": _decimal(sell.group(1))}
        if len(vals) >= 2:
            return {"buy": vals[0], "sell": vals[1]}
    raise MarketSourceError(f"AUTO no encontró compra/venta para {currency}.")


def _extract_html(html: str, config: dict) -> dict[str, dict[str, Decimal]]:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.stripped_strings)
    mode = str(config.get("mode", "AUTO")).upper()
    currencies = [str(x).upper() for x in config.get("currencies", ["USD", "EUR"])]
    out: dict[str, dict[str, Decimal]] = {}
    if mode == "AUTO":
        for cur in currencies:
            out[cur] = _auto_html(text, cur)
        return out
    mapping = config.get("mapping") or {}
    for cur in currencies:
        spec = mapping.get(cur) or mapping.get(cur.lower()) or {}

        if mode == "CSS":
            pair = {}
            for side in ("buy", "sell"):
                selector = spec.get(side)
                if not selector:
                    raise MarketSourceError(f"Falta selector CSS {cur}.{side}")
                node = soup.select_one(selector)
                if node is None:
                    raise MarketSourceError(f"Selector no encontrado: {selector}")
                pair[side] = _decimal(node.get("content") or node.get_text(" ", strip=True))
            out[cur] = pair
        elif mode == "REGEX":
            pattern = spec.get("regex")
            if not pattern:
                raise MarketSourceError(f"Falta regex para {cur}")
            m = re.search(pattern, text, re.I | re.S)
            if not m:
                raise MarketSourceError(f"Regex no encontró {cur}")
            gd = m.groupdict()
            if "buy" in gd and "sell" in gd:
                out[cur] = {"buy": _decimal(gd["buy"]), "sell": _decimal(gd["sell"])}
            elif len(m.groups()) >= 2:
                out[cur] = {"buy": _decimal(m.group(1)), "sell": _decimal(m.group(2))}
            else:
                raise MarketSourceError("Regex requiere grupos buy/sell o dos grupos posicionales.")
        else:
            raise MarketSourceError(f"Modo HTML no soportado: {mode}")
    return out


def _flatten_json(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    out=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            p=f"{prefix}.{k}" if prefix else str(k)
            out.extend(_flatten_json(v,p))
    elif isinstance(obj, list):
        for i,v in enumerate(obj[:50]):
            p=f"{prefix}[{i}]"
            out.extend(_flatten_json(v,p))
    else:
        out.append((prefix,obj))
    return out

def _auto_json(data: Any, currencies: list[str]) -> dict[str, dict[str, Decimal]]:
    flat=_flatten_json(data)
    out={}
    buy_words=('buy','compra','purchase','bid')
    sell_words=('sell','venta','sale','ask')
    for cur in currencies:
        c=cur.lower(); buy=[]; sell=[]
        for path,val in flat:
            lp=path.lower()
            if c not in lp: continue
            try: num=_decimal(val)
            except Exception: continue
            if any(w in lp for w in buy_words): buy.append((path,num))
            if any(w in lp for w in sell_words): sell.append((path,num))
        if buy and sell:
            out[cur]={'buy':buy[0][1],'sell':sell[0][1]}
    missing=[c for c in currencies if c not in out]
    if missing: raise MarketSourceError('AUTO JSON no encontró rutas compra/venta para: '+', '.join(missing))
    return out

def _extract_json(data: Any, config: dict) -> dict[str, dict[str, Decimal]]:
    mapping = config.get("mapping") or {}
    currencies = [str(x).upper() for x in config.get("currencies", mapping.keys() or ["USD", "EUR"])]
    if str(config.get("mode","MAPPING")).upper()=="AUTO":
        return _auto_json(data,currencies)
    out: dict[str, dict[str, Decimal]] = {}
    for cur in currencies:
        spec = mapping.get(cur) or mapping.get(cur.lower())
        if not spec:
            raise MarketSourceError(f"Falta mapping JSON para {cur}")
        out[cur] = {
            "buy": _decimal(_json_path(data, spec["buy"])),
            "sell": _decimal(_json_path(data, spec["sell"])),
        }
    return out


def fetch_source(source: dict, settings: Settings) -> SourceSnapshot:
    stype = str(source.get("source_type") or "WEB_HTML").upper()
    code = str(source.get("code") or source.get("name") or "SOURCE").upper()
    name = str(source.get("name") or code)
    if stype == "PRESET":
        cfg = _normalize_config(source)
        preset = str(cfg.get("preset") or code).upper()
        r = get_provider(preset, settings).fetch()
        if preset == "BCH":
            rates = {
                "USD": {"buy": Decimal(str(r.tcr)), "sell": Decimal(str(r.tcr))},
            }
        else:
            rates = {
                "USD": {"buy": Decimal(str(r.usd.buy)), "sell": Decimal(str(r.usd.sell))},
                "EUR": {"buy": Decimal(str(r.eur.buy)), "sell": Decimal(str(r.eur.sell))},
            }
        return SourceSnapshot(code, name, stype, r.source_url, r.fetched_at.isoformat(), rates, r.raw_hash)

    response = _fetch_http(source, settings)
    cfg = _normalize_config(source)
    if stype == "API_JSON":
        try:
            data = response.json()
        except Exception as exc:
            raise MarketSourceError("La URL no devolvió JSON válido.") from exc
        rates = _extract_json(data, cfg)
    elif stype == "WEB_HTML":
        rates = _extract_html(response.text, cfg)
    else:
        raise MarketSourceError(f"Tipo de fuente no soportado: {stype}")
    return SourceSnapshot(
        code=code,
        name=name,
        source_type=stype,
        source_url=response.url,
        fetched_at=datetime.now(ZoneInfo(settings.timezone)).isoformat(),
        rates=rates,
        raw_hash=hashlib.sha256(response.content).hexdigest(),
    )


def scan_source(source: dict, settings: Settings) -> dict[str, Any]:
    """Fetch and return a diagnostic preview without persisting configuration."""
    snap = fetch_source(source, settings)
    validate_snapshot_pairs(snap)
    return snap.serializable()


def validate_snapshot_pairs(snapshot: SourceSnapshot, max_pair_spread_percent: Decimal | str | float = "35.0") -> None:
    """Reject structurally implausible buy/sell pairs before consensus or UI approval."""
    limit = Decimal(str(max_pair_spread_percent))
    for cur, pair in snapshot.rates.items():
        buy = Decimal(str(pair.get("buy")))
        sell = Decimal(str(pair.get("sell")))
        if buy <= 0 or sell <= 0:
            raise MarketSourceError(f"{snapshot.code} {cur}: compra/venta debe ser mayor que cero.")
        if sell < buy:
            raise MarketSourceError(f"{snapshot.code} {cur}: venta {sell} es menor que compra {buy}.")
        spread = (sell - buy) / buy * Decimal("100")
        if spread > limit:
            raise MarketSourceError(
                f"{snapshot.code} {cur}: spread compra/venta {spread:.3f}% excede {limit}%."
            )


def build_consensus(store, settings: Settings, company: dict, currencies: list[str]) -> MarketConsensus:
    """Build a robust multi-source consensus without letting one bad secondary stop accounting.

    Blocking conditions:
    - fewer than the configured minimum raw/coherent sources;
    - official source unavailable for a requested currency;
    - official source is an outlier.

    Non-official outliers are excluded and surfaced as notices when enough
    coherent sources remain. The value written to SAP is always the official
    source sell rate; the median is only a plausibility control.
    """
    runtime_settings = store.get_settings()
    max_pair_spread = Decimal(str(runtime_settings.get("max_pair_spread_percent", "35.0")))
    configured = [x.strip().upper() for x in str(company.get("bank_source_codes") or "").split(",") if x.strip()]
    primary = str(company.get("primary_bank") or "").upper().strip()
    if primary and primary not in configured:
        configured.insert(0, primary)
    configured = list(dict.fromkeys(configured))
    if len(configured) < 3:
        return MarketConsensus(
            False, primary, {}, {}, {}, [], {},
            ["Configure al menos 3 fuentes bancarias para esta base."], [], []
        )

    sources = {s["code"].upper(): s for s in store.list_bank_sources(enabled_only=True)}
    snapshots: list[SourceSnapshot] = []
    failed: dict[str, str] = {}
    for code in configured:
        src = sources.get(code)
        if not src:
            failed[code] = "Fuente inexistente o deshabilitada"
            continue
        try:
            # Always perform a fresh network fetch. The shared HTTP client sends
            # no-cache headers so a previous day's page is not intentionally reused.
            snap = fetch_source(src, settings)
            validate_snapshot_pairs(snap, max_pair_spread)
            observed_day = datetime.now(ZoneInfo(settings.timezone)).date().isoformat()
            store.record_market_snapshot(
                observed_day=observed_day,
                fetched_at=snap.fetched_at,
                source_code=snap.code,
                source_name=snap.name,
                source_url=snap.source_url,
                rates=snap.rates,
                raw_hash=snap.raw_hash,
            )
            snapshots.append(snap)
            store.mark_bank_source_result(src["id"], True, "OK")
        except Exception as exc:
            failed[code] = str(exc)
            store.mark_bank_source_result(src["id"], False, str(exc))

    warnings: list[str] = []
    notices: list[str] = []
    official_rates: dict[str, Decimal] = {}
    medians: dict[str, Decimal] = {}
    deviations: dict[str, Decimal] = {}
    max_dev = Decimal(str(runtime_settings.get("max_source_deviation_percent", settings.max_bank_spread_percent)))
    min_sources = max(3, int(runtime_settings.get("min_market_sources", "3") or 3))
    by_code = {s.code.upper(): s for s in snapshots}

    if primary not in by_code:
        warnings.append(f"La fuente oficial {primary or '(sin definir)'} no respondió correctamente.")

    for cur in [c.upper() for c in currencies]:
        values: list[tuple[str, Decimal]] = []
        for snap in snapshots:
            pair = snap.rates.get(cur)
            if pair and pair.get("sell") is not None:
                values.append((snap.code.upper(), Decimal(str(pair["sell"]))))

        if len(values) < min_sources:
            warnings.append(f"{cur}: sólo {len(values)} fuentes válidas; se requieren {min_sources}.")
            continue

        value_by_code = dict(values)
        if primary not in value_by_code:
            warnings.append(f"{cur}: la fuente oficial {primary or '(sin definir)'} no publicó una tasa de venta.")
            continue

        initial_median = Decimal(str(median([value for _, value in values])))
        deviation_by_code = {
            code: ((abs(value - initial_median) / initial_median) * Decimal("100")) if initial_median else Decimal("999")
            for code, value in values
        }
        inliers = [(code, value) for code, value in values if deviation_by_code[code] <= max_dev]
        outliers = [(code, value) for code, value in values if deviation_by_code[code] > max_dev]

        official_initial_dev = deviation_by_code.get(primary, Decimal("999"))
        if official_initial_dev > max_dev:
            warnings.append(
                f"{cur}: fuente oficial difiere {official_initial_dev:.3f}% del consenso "
                f"({primary}; máx. {max_dev}%)."
            )

        if len(inliers) < min_sources:
            warnings.append(
                f"{cur}: sólo {len(inliers)} fuentes coherentes después de excluir outliers; "
                f"se requieren {min_sources}."
            )

        secondary_outliers = [(code, value) for code, value in outliers if code != primary]
        if secondary_outliers:
            details = ", ".join(
                f"{code} ({deviation_by_code[code]:.3f}% vs mediana)"
                for code, _ in secondary_outliers
            )
            notices.append(f"{cur}: fuentes secundarias excluidas por outlier: {details}.")

        # Never make the official rate actionable unless the official source is
        # coherent and the remaining market set still satisfies the minimum.
        if official_initial_dev > max_dev or len(inliers) < min_sources:
            continue

        cleaned_median = Decimal(str(median([value for _, value in inliers])))
        official = value_by_code[primary]
        official_clean_dev = (
            (abs(official - cleaned_median) / cleaned_median) * Decimal("100")
            if cleaned_median else Decimal("999")
        )
        if official_clean_dev > max_dev:
            warnings.append(
                f"{cur}: fuente oficial difiere {official_clean_dev:.3f}% "
                f"de la mediana depurada ({primary}; máx. {max_dev}%)."
            )
            continue

        medians[cur] = cleaned_median
        official_rates[cur] = official
        deviations[cur] = official_clean_dev

    if failed:
        notices.append(
            "Fuentes no disponibles o inválidas excluidas: "
            + ", ".join(f"{code} ({reason})" for code, reason in sorted(failed.items()))
        )

    safe = not warnings and all(cur.upper() in official_rates for cur in currencies)
    return MarketConsensus(
        safe=safe,
        official_source=primary,
        official_rates=official_rates,
        medians=medians,
        deviations_percent=deviations,
        successful_sources=[s.code for s in snapshots],
        failed_sources=failed,
        warnings=warnings,
        snapshots=snapshots,
        notices=notices,
    )

