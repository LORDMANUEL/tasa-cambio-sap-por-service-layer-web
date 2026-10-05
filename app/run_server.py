"""Uvicorn entry point for the local-only SAP FX V5 web service."""
import uvicorn
from app.config import get_settings

s=get_settings()
if __name__=="__main__":
    uvicorn.run("app.main:app",host="127.0.0.1",port=s.app_port,reload=False,access_log=True)
