"""Create local development secrets once, without displaying their values."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
p=root/'.env'
if p.exists():
    print('Configuração .env existente preservada.')
else:
    p.write_text('POSTGRES_PASSWORD='+secrets.token_hex(32)+'\nAPP_ENV=development\n')
    p.chmod(0o600)
    print('Arquivo .env criado com senha aleatória. Não o publique nem envie ao Git.')
