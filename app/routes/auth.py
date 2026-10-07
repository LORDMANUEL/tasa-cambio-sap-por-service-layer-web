"""Authentication routes for the Atas web UI."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.web_auth import COOKIE, sign_session, verify_password


def create_auth_router(settings, setup_complete, organization_name, logo_url) -> APIRouter:
    router=APIRouter()

    @router.get("/login",response_class=HTMLResponse)
    def login_page():
        if not setup_complete():
            return RedirectResponse("/setup",303)
        org=organization_name()
        logo=logo_url()
        brand=(
            f"<img class='login-org-logo' src='{logo}'>"
            if logo else "<div class='brand-mark xl'>FX</div>"
        )
        return HTMLResponse(
            f"""<!doctype html><html lang='es' data-theme='dark'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Atas · Acceso</title><link rel='stylesheet' href='/static/styles.css'><script src='/static/app.js' defer></script></head><body><div class='login-v5'><section class='login-visual'>{brand}<div><div class='eyebrow'>SAP BUSINESS ONE · DAILY FX</div><h1>Control de tasas simple, visual y trazable.</h1><p>{org}</p></div><div class='login-flow'><span>Banco</span><i>→</i><span>Validación</span><i>→</i><span>SAP</span><i>→</i><span>Auditoría</span></div></section><section class='login-form-wrap'><form method='post' class='login-card v5'><div class='eyebrow'>ACCESO LOCAL</div><h2>Bienvenido</h2><p class='muted'>Ingresa para administrar tasas y automatizaciones.</p><label>Usuario</label><input name='user' autocomplete='username' required><label>Contraseña</label><input type='password' name='password' autocomplete='current-password' required><button class='btn primary xl'>Ingresar →</button><small>Panel local · secretos cifrados por el sistema operativo</small></form></section></div></body></html>"""
        )

    @router.post("/login")
    async def login(req: Request):
        if not setup_complete():
            return RedirectResponse("/setup",303)
        form=await req.form()
        user=str(form.get("user",""))
        password=str(form.get("password",""))
        if user!=settings.web_admin_user or not verify_password(password,settings.web_admin_password_hash):
            return HTMLResponse("Credenciales inválidas",401)
        response=RedirectResponse("/",303)
        response.set_cookie(
            COOKIE,
            sign_session(user,settings.web_session_secret),
            httponly=True,
            samesite="strict",
            secure=False,
            max_age=28800,
        )
        return response

    @router.get("/logout")
    def logout():
        response=RedirectResponse("/login",303)
        response.delete_cookie(COOKIE)
        return response

    return router
