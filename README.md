# P4 Consultores

Sistema web de planejamento financeiro anual: React/TypeScript, FastAPI, PostgreSQL, migrações Alembic e PDF no servidor. Autenticação real, permissões verificadas na API, salvamento automático com confirmação e controle de conflitos. Sessões abertas não expiram por tempo; a validade anual administrativa do aluno é independente.

Esta é uma **reconstrução** a partir dos anexos preservados. Os arquivos agora estão em commits Git; não dependem somente do snapshot da máquina. O código está na branch `codex/p4-reconstrucao-20261103` do repositório `andrecarroni/PLAN`, com envio remoto autorizado pelo usuário e confirmado. Consulte a comprovação de preservação e as limitações em `docs/validacao.md`.

## Início rápido no seu computador

Instale Docker com Compose v2 e Python 3. Extraia o ZIP do código ou clone a branch de recuperação. No terminal, dentro da pasta do projeto:

```sh
python3 scripts/configure.py
docker compose up --build -d
docker compose exec web python -m app.cli create-admin
docker compose exec web python -m app.cli seed-course
```

No Windows com Python instalado pelo launcher, use `py scripts/configure.py` no primeiro comando. A criação do administrador pergunta nome, celular internacional e senha oculta; não existe senha fixa de produção. A aplicação usa a porta 8000 somente no computador em que esses comandos são executados. `seed-course` cria sete rascunhos; não publica conteúdo automaticamente.

Veja [PASSO A PASSO](docs/PASSO-A-PASSO.md) para instruções de preservação, uso, logo e hospedagem pública. Publicar o ambiente de desenvolvimento não publica o site para alunos.

## Desenvolvimento

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
npm ci --prefix frontend
npm run build --prefix frontend
python3 scripts/configure.py
docker compose up -d --wait db
python3 scripts/run.py alembic upgrade head
python3 scripts/run.py app.cli seed-course
python3 scripts/run.py
```

Em outro terminal, `npm run dev --prefix frontend` permite recarga da interface; o proxy `/api` encaminha para o backend. Os scripts `run.py` usam o banco local da configuração `.env` sem imprimir a senha. O comando sem argumentos inicia o servidor. Na nuvem, o instalador preserva também a configuração local em `/workspace/shared/p4-consultores/config.env`, fora do checkout; não exiba esse arquivo. Isso permite recriar `.env` após uma restauração sem trocar a senha do banco preservado. `scripts/cloud-install.sh` reproduz o setup desta nuvem, preservando a configuração existente e sem criar contas reais.

Sem `DATABASE_URL`, o backend aceita SQLite em `/tmp/p4-dev.db` somente para desenvolvimento. Produção recusa SQLite. Instantes em UTC; datas administrativas referenciadas em Brasília. Valores financeiros persistidos como `NUMERIC(16,2)` e calculados com `Decimal`.

API documentada em `/api/docs`; prontidão em `/api/health`, que verifica o banco e a tabela de usuários. Sem login, rotas financeiras retornam 401; permissões insuficientes retornam 403.

## Testes reais e demonstração

```sh
# Banco p4_test exclusivo; nunca use produção.
docker compose exec -T db createdb -U p4 p4_test
python3 scripts/test.py
npm run build --prefix frontend
```

Se `p4_test` já existir, não repita o `createdb`. A suíte recria somente o esquema de teste. `TEST_DATABASE_URL` precisa apontar para um banco cujo nome contenha `test`; `DATABASE_URL` de produção é ignorada pela fixture. Para conveniência SQLite: `cd backend && ../.venv/bin/python -m pytest tests -q`.

Para criar dados fictícios, **somente em banco de demonstração separado**:

```sh
docker compose exec -e ALLOW_DEMO=1 web python -m app.cli demo
```

As senhas são aleatórias e aparecem uma vez na saída local do comando. Guarde-as com cuidado; não envie para o Git. O comando se recusa a executar com `APP_ENV=production`. Não execute no banco de alunos reais. O script opcional `scripts/browser_smoke.py` usa Playwright e Chromium para verificar os fluxos completos; as instruções estão em `docs/validacao.md`.

## Documentação

- [Passo a passo manual](docs/PASSO-A-PASSO.md).
- [Cálculos e mapeamento da planilha/curso](docs/calculos.md).
- [Permissões, recuperação e validade](docs/permissoes.md).
- [Implantação, backup, restauração e retenção](docs/operacao.md).
- [Validação desta reconstrução](docs/validacao.md).
- [Roteiro de validação humana com a equipe](docs/roteiro-validacao-equipe.md).

Sem rede, valores não confirmados ficam apenas na memória da página, com aviso ao sair. Não há promessa de armazenamento offline. Nenhuma informação financeira é gravada em localStorage. Conflitos HTTP 409 exigem decisão explícita antes de recarregar; não são sobrescritos silenciosamente.

A logo original foi enviada na conversa, mas não existe como arquivo nos anexos preservados. Há identificação tipográfica temporária. Inclua o arquivo original em `frontend/public/logo.png`; ele será usado na interface e no PDF, sem redesenho. Configure o canal real de suporte e revise os rascunhos antes do piloto.

## Windows e certificados da nuvem

O Compose padrão não requer arquivos de certificados do host. O Dockerfile usa os certificados padrão das imagens; certificados extras são opcionais e não desativam TLS. Para erro `failed to execute bake`, siga [Windows: Docker](docs/WINDOWS-DOCKER.md): construa com `docker build --progress=plain -t p4-consultores:rebuild .` e depois inicie com `docker compose up --no-build --pull never -d`.

Somente para builds neste ambiente gerenciado, use `compose.cloud.yaml` e defina `P4_PROXY_CA`/`P4_CA_BUNDLE`, conforme o guia. Esses arquivos extras não são necessários na instalação normal do Windows.
