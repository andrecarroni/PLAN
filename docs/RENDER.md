# Inicialização no Render

Use Docker, a branch `codex/p4-reconstrucao-20261103`, Dockerfile `./Dockerfile`, contexto na raiz e plano Free. Defina `APP_ENV=production` e `DATABASE_URL` com a conexão Neon `postgresql+psycopg://...`, mantendo os parâmetros TLS. Nunca salve essa conexão no GitHub.

Em **Docker Command**, informe somente:

```text
/bin/sh /app/backend/start-render.sh
```

O script aplica migrações antes de iniciar o servidor. Se a migração falhar, o servidor não inicia. A porta segue `PORT` do Render, com padrão 10000. Health Check Path: `/api/health`. Pre-Deploy Command vazio. Auto-Deploy Off para atualizações manuais.

O comando anterior com `sh -c` e aspas foi interpretado incorretamente pelo campo Docker Command no primeiro deploy (código 127). O arquivo evita a necessidade de passar uma expressão de shell nesse campo.

Após salvar, use **Manual Deploy → Deploy latest commit**, para incluir o novo arquivo na imagem; reiniciar a imagem antiga não basta. A construção não transfere dados locais: o administrador, conteúdo e configurações precisam ser migrados separadamente antes da abertura aos alunos.
