"""Interactive utility that creates or replaces the local web administrator credentials."""
from __future__ import annotations
import getpass,secrets
from pathlib import Path
from app.config import BASE_DIR
from app.web_auth import password_hash

def set_env(path:Path,key:str,value:str):
    lines=path.read_text(encoding='utf-8').splitlines() if path.exists() else []; out=[]; found=False
    for line in lines:
        if line.startswith(key+'='): out.append(f'{key}={value}'); found=True
        else: out.append(line)
    if not found: out.append(f'{key}={value}')
    path.write_text('\n'.join(out)+'\n',encoding='utf-8')

def main():
    env=BASE_DIR/'.env'; user=input('Usuario administrador web [admin]: ').strip() or 'admin'
    while True:
        p1=getpass.getpass('Nueva contraseña web (mín. 10 caracteres): '); p2=getpass.getpass('Repita contraseña: ')
        if p1==p2 and len(p1)>=10: break
        print('No coinciden o son muy cortas.')
    set_env(env,'WEB_ADMIN_USER',user); set_env(env,'WEB_ADMIN_PASSWORD_HASH',password_hash(p1)); content=env.read_text(encoding='utf-8'); current=''
    for line in content.splitlines():
        if line.startswith('WEB_SESSION_SECRET='): current=line.split('=',1)[1].strip(); break
    if not current: set_env(env,'WEB_SESSION_SECRET',secrets.token_urlsafe(48))
    print('[OK] Administrador web configurado.')
if __name__=='__main__': main()
