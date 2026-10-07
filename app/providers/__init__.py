"""Bank-provider factory used to resolve configured automatic exchange-rate connectors."""
from app.config import Settings
from .banpais import BanpaisProvider
from .ficohsa import FicohsaProvider
from .bch import BchProvider

def get_provider(name: str, settings: Settings):
    name=name.upper()
    if name=="BANPAIS": return BanpaisProvider(settings)
    if name=="FICOHSA": return FicohsaProvider(settings)
    if name=="BCH": return BchProvider(settings)
    raise ValueError(f"Proveedor automático no soportado: {name}")
