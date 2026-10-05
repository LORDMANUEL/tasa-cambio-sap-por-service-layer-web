# THIRD_PARTY_NOTICES.md

Atas incorpora o depende de software y servicios de terceros. Esos componentes **no quedan relicenciados** por la licencia propietaria de Atas y conservan sus propias licencias y avisos.

Las dependencias directas del runtime se declaran en `requirements-runtime.txt`, y las dependencias de desarrollo/prueba en `requirements.txt`.

La distribución puede incluir, entre otros:

- Python runtime;
- FastAPI;
- Uvicorn;
- Requests;
- Beautiful Soup;
- python-dotenv;
- Pydantic / pydantic-settings;
- python-multipart;
- tzdata;
- cryptography;
- dependencias transitivas instaladas por esas bibliotecas.

Antes de redistribuir un build comercial o a terceros debe conservarse cualquier aviso que exija la licencia de cada dependencia y revisar las licencias efectivas de la versión incluida en el build.

SAP, SAP Business One y cualquier otra marca mencionada pertenecen a sus respectivos titulares. Atas no concede derechos sobre marcas, APIs, sitios web, datos ni servicios de terceros.
