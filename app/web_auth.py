"""Password hashing, signed sessions and cookie authentication for the local administration UI."""
from __future__ import annotations
import base64, hashlib, hmac, os, secrets, time
from fastapi import Request
from fastapi.responses import RedirectResponse

COOKIE="tasa_v4_session"

def password_hash(password: str, salt: bytes|None=None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 250_000)
    return "pbkdf2_sha256$250000$"+base64.b64encode(salt).decode()+"$"+base64.b64encode(dk).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        alg, rounds, salt, digest = encoded.split("$",3)
        if alg!="pbkdf2_sha256": return False
        test=hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(rounds))
        return hmac.compare_digest(test, base64.b64decode(digest))
    except Exception: return False

def sign_session(user: str, secret: str, ttl: int=28800) -> str:
    exp=str(int(time.time())+ttl); nonce=secrets.token_urlsafe(12); payload=f"{user}|{exp}|{nonce}"
    sig=hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()

def verify_session(token: str|None, secret: str, expected_user: str) -> bool:
    if not token: return False
    try:
        raw=base64.urlsafe_b64decode(token.encode()).decode(); user,exp,nonce,sig=raw.rsplit("|",3)
        payload=f"{user}|{exp}|{nonce}"; expected=hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()
        return user==expected_user and int(exp)>=int(time.time()) and hmac.compare_digest(sig,expected)
    except Exception: return False

def require_web(request: Request, user: str, secret: str):
    if not verify_session(request.cookies.get(COOKIE), secret, user):
        return RedirectResponse("/login", status_code=303)
    return None
