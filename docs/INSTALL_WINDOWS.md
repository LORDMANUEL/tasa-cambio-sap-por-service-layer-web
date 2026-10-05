# Instalación en Windows

La distribución de Windows se genera como `Atas-V5-Setup-x64.exe`.

## Qué incluye

- Atas V5.
- Python 3.13 embebido x64.
- Dependencias Python preinstaladas.
- Acceso directo opcional.
- Lanzador que inicia el servidor local y abre `http://127.0.0.1:8787/`.

No requiere una instalación previa de Python.

## Primera ejecución

1. Ejecute el instalador.
2. Abra **Atas**.
3. Complete empresa/logo, administrador, SMTP opcional, Service Layer, CompanyDB y mínimo 3 fuentes.
4. El servicio web escucha únicamente en `127.0.0.1`.

Los datos quedan dentro del perfil local donde se instala.


## Edición Portable

GitHub Actions también genera:

```text
Atas-V5-Portable-x64.zip
```

No instala Python. El ZIP ya contiene:

```text
runtime/python/python.exe
runtime/python/Lib/site-packages/
app/
scripts/windows/start-atas.cmd
```

Uso:

1. Descomprima el ZIP.
2. Ejecute `scripts\windows\start-atas.cmd`.
3. Atas abre `http://127.0.0.1:8787/`.

El workflow extrae el ZIP en un directorio limpio, ejecuta el Python embebido y exige que `/health` responda `status=ok` y `service=Atas` antes de publicar el artifact.
