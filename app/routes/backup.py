"""Backup routes for the Atas web UI."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.backup_manager import BackupError, create_backup
from app.dashboard import esc


def create_backup_router(settings, store_provider, authed, redirect_login, ui) -> APIRouter:
    """Build backup routes without coupling them to app.main globals."""
    router=APIRouter()

    @router.post("/settings/backup",response_class=HTMLResponse)
    def settings_backup(req: Request):
        if not authed(req):
            return redirect_login()
        try:
            store=store_provider()
            result=create_backup(settings,store.path)
        except BackupError as exc:
            return HTMLResponse(
                ui(
                    "Backup",
                    f"<div class='card error-panel'><h2>Backup fallido</h2>"
                    f"<p>{esc(exc)}</p><a class='btn' href='/settings'>Volver</a></div>",
                ),
                500,
            )
        return HTMLResponse(
            ui(
                "Backup",
                f"<div class='card success-panel'><h2>Backup verificado</h2>"
                f"<p><b>{esc(result['name'])}</b></p>"
                f"<p>SHA-256: <code>{esc(result['sha256'])}</code></p>"
                f"<p>Guardado en <code>{esc(result['path'])}</code>.</p>"
                "<p class='muted'>Contiene información sensible. "
                "No lo publique ni lo adjunte a tickets.</p>"
                "<a class='btn primary' href='/settings'>Volver</a></div>",
            )
        )

    return router
