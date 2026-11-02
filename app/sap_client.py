"""Cliente SAP Business One Service Layer para SAP FX Control Center V5.

Contrato validado contra el $metadata del sistema y probado manualmente en Postman:
- OData v2 lectura: GET /b1s/v2/SBOBobService_GetCurrencyRate(Currency='USD',Date='YYYYMMDD')
- OData v1 lectura: POST /b1s/v1/SBOBobService_GetCurrencyRate con Currency/Date
- Ausencia: HTTP 400, error.code == -4006, message == 'Update the exchange rate'
- Escritura: POST /b1s/v2/SBOBobService_SetCurrencyRate
- Verificación: repetir el GET y comparar el Edm.Double devuelto.

No se registran passwords, cookies ni SessionId.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import logging
import re
import requests
import urllib3

log = logging.getLogger(__name__)


class SapError(RuntimeError):
    pass


@dataclass(frozen=True)
class SapCompany:
    company_db: str
    environment: str
    allow_write: bool


class SapFxClient:
    def __init__(self, base_url: str, company: SapCompany, user: str, password: str,
                 verify_tls: bool = True, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.company = company
        self.user = user
        self._password = password
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
        self.logged_in = False
        if not verify_tls:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            log.warning("SAP TLS certificate verification DISABLED company=%s url=%s",
                        company.company_db, self.base_url)

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _request(self, method: str, endpoint: str, *, payload: dict | None = None) -> requests.Response:
        try:
            r = self.session.request(method, self._url(endpoint), json=payload,
                                     timeout=self.timeout, verify=self.verify_tls)
        except requests.RequestException as exc:
            raise SapError(f"Error de red hacia Service Layer ({self.company.company_db}): {exc}") from exc
        ctype = r.headers.get("Content-Type", "")
        log.debug("SAP response company=%s method=%s endpoint=%s status=%s content_type=%s bytes=%s",
                  self.company.company_db, method, endpoint, r.status_code, ctype, len(r.content or b""))
        if r.status_code >= 400:
            code, message = _sap_error(r)
            suffix = f" SAP={code}" if code is not None else ""
            raise SapError(f"Service Layer HTTP {r.status_code}{suffix} en {endpoint}: {message}")
        return r

    def login(self) -> None:
        payload = {"CompanyDB": self.company.company_db, "UserName": self.user, "Password": self._password}
        r = self._request("POST", "Login", payload=payload)
        body = _json_or_none(r)
        if not isinstance(body, dict) or not body.get("SessionId"):
            raise SapError("Login SAP exitoso HTTP pero sin SessionId interpretable.")
        self.logged_in = True
        log.info("SAP login OK company=%s environment=%s", self.company.company_db, self.company.environment)

    def logout(self) -> None:
        if not self.logged_in:
            return
        try:
            self._request("POST", "Logout")
        except SapError as exc:
            log.warning("SAP logout warning company=%s error=%s", self.company.company_db, exc)
        finally:
            self.logged_in = False
            self.session.close()

    @property
    def odata_version(self) -> str:
        match = re.search(r"/(v\d+)$", self.base_url, re.I)
        return match.group(1).lower() if match else "v2"

    def get_local_currency(self) -> str:
        """Read the company local currency using the canonical Service Layer action.

        SAP's current v2 reference documents SBOBobService_GetLocalCurrency as POST.
        Some older Service Layer builds also expose the OData FunctionImport as GET,
        so v2 falls back to GET only when the canonical action is not accepted.
        """
        self._ensure_login()
        if self.odata_version == "v1":
            r = self._request("POST", "SBOBobService_GetLocalCurrency", payload={})
            return str(_extract_scalar(r, text_ok=True)).strip()

        r = self.session.post(
            self._url("SBOBobService_GetLocalCurrency"),
            json={},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=self.timeout,
            verify=self.verify_tls,
        )
        if r.status_code < 400:
            return str(_extract_scalar(r, text_ok=True)).strip()
        if r.status_code not in {400, 404, 405, 501}:
            code, message = _sap_error(r)
            raise SapError(f"Service Layer HTTP {r.status_code} SAP={code} leyendo moneda local: {message}")

        fallback = self.session.get(
            self._url("SBOBobService_GetLocalCurrency()"),
            headers={"Accept": "application/json"},
            timeout=self.timeout,
            verify=self.verify_tls,
        )
        if fallback.status_code >= 400:
            code, message = _sap_error(fallback)
            raise SapError(f"Service Layer HTTP {fallback.status_code} SAP={code} leyendo moneda local: {message}")
        return str(_extract_scalar(fallback, text_ok=True)).strip()

    def get_currency_rate(self, currency: str, rate_date: date) -> Decimal:
        """Return the SAP rate or Decimal('0') when SAP reports -4006.

        v1 uses the action POST. v2 prefers the canonical POST documented by SAP
        and falls back to the historical FunctionImport GET for compatibility
        with installations where that route was previously validated.
        """
        self._ensure_login()
        cur = currency.upper().strip()
        if not re.fullmatch(r"[A-Z]{3}", cur):
            raise SapError(f"Código de moneda inválido: {currency!r}")
        ymd = rate_date.strftime("%Y%m%d")
        payload = {"Currency": cur, "Date": ymd}

        if self.odata_version == "v1":
            try:
                r = self.session.post(
                    self._url("SBOBobService_GetCurrencyRate"),
                    json=payload,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
            except requests.RequestException as exc:
                raise SapError(f"Error de red leyendo {cur}: {exc}") from exc
            return _parse_currency_rate_response(r, cur, ymd)

        # SAP Business One v2 canonical action (OData v4).
        try:
            r = self.session.post(
                self._url("SBOBobService_GetCurrencyRate"),
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self.timeout,
                verify=self.verify_tls,
            )
        except requests.RequestException as exc:
            raise SapError(f"Error de red leyendo {cur}: {exc}") from exc

        if r.status_code == 200 or _is_missing_rate_response(r):
            return _parse_currency_rate_response(r, cur, ymd)

        # Compatibility path for Service Layer installations exposing the
        # historical FunctionImport GET instead of/alongside the canonical action.
        if r.status_code not in {400, 404, 405, 501}:
            return _parse_currency_rate_response(r, cur, ymd)

        fallback_endpoints = (
            f"SBOBobService_GetCurrencyRate(Currency='{cur}',Date='{ymd}')",
            f"SBOBobService_GetCurrencyRate(Currency={cur},Date={ymd})",
        )
        last = r
        for endpoint in fallback_endpoints:
            try:
                last = self.session.get(
                    self._url(endpoint),
                    headers={"Accept": "application/json"},
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
            except requests.RequestException as exc:
                raise SapError(f"Error de red leyendo {cur}: {exc}") from exc
            if last.status_code == 200 or _is_missing_rate_response(last):
                return _parse_currency_rate_response(last, cur, ymd)
            if last.status_code not in {400, 404, 405, 501}:
                break
        return _parse_currency_rate_response(last, cur, ymd)

    def set_currency_rate(self, currency: str, rate_date: date, rate: Decimal) -> None:
        self._ensure_login()
        if not self.company.allow_write:
            raise SapError(f"ESCRITURA BLOQUEADA para {self.company.company_db} ({self.company.environment}).")
        if rate <= 0:
            raise SapError("La tasa a escribir debe ser mayor que cero.")
        cur = currency.upper().strip()
        if not re.fullmatch(r"[A-Z]{3}", cur):
            raise SapError(f"Código de moneda inválido: {currency!r}")
        payload = {"RateDate": rate_date.strftime("%Y%m%d"), "Currency": cur, "Rate": format(rate, "f")}
        r = self._request("POST", "SBOBobService_SetCurrencyRate", payload=payload)
        log.info("SAP rate write accepted company=%s currency=%s date=%s status=%s",
                 self.company.company_db, cur, rate_date.isoformat(), r.status_code)

    def _ensure_login(self) -> None:
        if not self.logged_in:
            raise SapError("La sesión SAP no está autenticada.")

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.logout()



def _is_missing_rate_response(r: requests.Response) -> bool:
    code, _ = _sap_error(r)
    return r.status_code == 400 and str(code) == "-4006"


def _parse_currency_rate_response(r: requests.Response, currency: str, ymd: str) -> Decimal:
    if r.status_code == 200:
        value = _extract_scalar(r, text_ok=False)
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise SapError(f"Tasa {currency} no interpretable: {r.text[:300]}") from exc
    code, message = _sap_error(r)
    if r.status_code == 400 and str(code) == "-4006":
        log.info("SAP rate missing currency=%s date=%s code=-4006", currency, ymd)
        return Decimal("0")
    raise SapError(f"Service Layer HTTP {r.status_code} SAP={code} leyendo {currency}: {message}")


def _json_or_none(r: requests.Response):
    try:
        return r.json()
    except Exception:
        return None


def _sap_error(r: requests.Response) -> tuple[str | int | None, str]:
    body = _json_or_none(r)
    if isinstance(body, dict):
        err = body.get("error", body)
        if isinstance(err, dict):
            return err.get("code"), str(err.get("message") or "Error SAP sin mensaje")
    text = (r.text or "").strip().replace("\r", " ").replace("\n", " ")
    return None, text[:500] or "Error SAP sin body"


def _extract_scalar(r: requests.Response, *, text_ok: bool):
    body = _json_or_none(r)
    if isinstance(body, (int, float, str)):
        return body
    if isinstance(body, dict):
        for key in ("value", "CurrencyRate", "Rate", "LocalCurrency", "Currency"):
            if key in body and not isinstance(body[key], (dict, list)):
                return body[key]
        d = body.get("d")
        if isinstance(d, (int, float, str)):
            return d
        if isinstance(d, dict):
            for key in ("value", "CurrencyRate", "Rate", "LocalCurrency", "Currency"):
                if key in d and not isinstance(d[key], (dict, list)):
                    return d[key]
    raw = (r.text or "").strip().strip('"')
    if not raw:
        raise SapError("Service Layer devolvió respuesta vacía.")
    if text_ok:
        return raw
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", raw):
        return raw
    raise SapError(f"Respuesta escalar no reconocida: {raw[:300]}")
