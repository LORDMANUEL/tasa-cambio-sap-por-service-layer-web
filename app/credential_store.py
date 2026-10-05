"""Cross-platform encryption for SAP/SMTP/API secrets."""
from __future__ import annotations
import base64,ctypes,os
from pathlib import Path
from ctypes import wintypes
class CredentialError(RuntimeError): pass
if os.name=='nt':
    class DATA_BLOB(ctypes.Structure): _fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_byte))]
    crypt32=ctypes.windll.crypt32; kernel32=ctypes.windll.kernel32
    def _blob(data:bytes):
        buf=ctypes.create_string_buffer(data); return DATA_BLOB(len(data),ctypes.cast(buf,ctypes.POINTER(ctypes.c_byte))),buf
    def encrypt_secret(secret:str)->str:
        src,keep=_blob(secret.encode()); out=DATA_BLOB()
        if not crypt32.CryptProtectData(ctypes.byref(src),'Atas V5',None,None,None,0,ctypes.byref(out)): raise CredentialError('DPAPI no pudo cifrar la credencial')
        try:return 'dpapi:'+base64.b64encode(ctypes.string_at(out.pbData,out.cbData)).decode('ascii')
        finally:kernel32.LocalFree(out.pbData)
    def decrypt_secret(blob:str)->str:
        if not blob.startswith('dpapi:'): raise CredentialError('Formato de credencial DPAPI inválido')
        src,keep=_blob(base64.b64decode(blob.split(':',1)[1])); out=DATA_BLOB()
        if not crypt32.CryptUnprotectData(ctypes.byref(src),None,None,None,None,0,ctypes.byref(out)): raise CredentialError('DPAPI no pudo descifrar la credencial')
        try:return ctypes.string_at(out.pbData,out.cbData).decode()
        finally:kernel32.LocalFree(out.pbData)
else:
    from cryptography.fernet import Fernet,InvalidToken
    BASE=Path(__file__).resolve().parent.parent
    def _key_file(): return Path(os.environ.get('SAPFX_FERNET_KEY_FILE','').strip() or (BASE/'data'/'.credential.key'))
    def _fernet():
        p=_key_file(); p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists(): p.write_bytes(Fernet.generate_key()); p.chmod(0o600)
        return Fernet(p.read_bytes().strip())
    def encrypt_secret(secret:str)->str:return 'fernet:'+_fernet().encrypt(secret.encode()).decode('ascii')
    def decrypt_secret(blob:str)->str:
        if not blob.startswith('fernet:'): raise CredentialError('Formato de credencial Fernet inválido')
        try:return _fernet().decrypt(blob.split(':',1)[1].encode()).decode()
        except InvalidToken as exc: raise CredentialError('La credencial no pertenece a esta instalación') from exc
