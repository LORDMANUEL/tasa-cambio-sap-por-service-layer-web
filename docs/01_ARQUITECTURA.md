# Arquitectura V5

```text
Fuentes de mercado (API / HTML / presets)
          ↓
Extracción + Decimal + Consenso 3+
          ↓
Sync Engine
   ├─ SAP Business One Service Layer
   ├─ SQLite / Auditoría
   └─ SMTP saliente opcional

FastAPI local 127.0.0.1
  ├─ Wizard inicial
  ├─ Dashboard
  ├─ Bases SAP / Multiempresa
  ├─ Automatización
  ├─ Bancos y fuentes
  ├─ Transacciones / Reportes
  ├─ Configuración / Branding / SMTP
  └─ Logs
```

El motor SAP usa `SBOBobService_GetCurrencyRate` y `SBOBobService_SetCurrencyRate`. Cada escritura se vuelve a leer antes de marcarse como verificada.
