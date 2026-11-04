# Windows: erro de Bake e certificado no Docker

Se `docker compose build` falhar imediatamente com `failed to execute bake`, use a construção direta. Algumas versões do Docker Desktop continuam usando Bake mesmo com `COMPOSE_BAKE=false`.

O Dockerfile foi corrigido para usar os certificados padrão das imagens quando os certificados extras da nuvem não são fornecidos. A verificação TLS permanece habilitada. As montagens exclusivas da nuvem ficam em `compose.cloud.yaml`, separado do Compose padrão.

## Atualizar a pasta já baixada sem perder a configuração

1. No GitHub, abra a branch `codex/p4-reconstrucao-20261103`.
2. Abra o arquivo **Dockerfile** e copie o conteúdo inteiro, pelo botão de copiar o arquivo.
3. No PowerShell já aberto na pasta do projeto, execute `notepad .\Dockerfile`.
4. No Bloco de Notas, pressione Ctrl+A, cole o conteúdo atualizado, pressione Ctrl+S e feche. Confira que o nome continua `Dockerfile`, sem extensão `.txt`.
5. Para atualizar também o fluxo padrão de Compose, repita a cópia do arquivo **compose.yaml** do GitHub, abrindo localmente com `notepad .\compose.yaml`. Não substitua o arquivo `.env`.
6. Execute uma linha por vez:

   ```powershell
   docker build --progress=plain -t p4-consultores:rebuild .
   ```

   Aguarde terminar. Somente se houver sucesso:

   ```powershell
   docker compose up --no-build --pull never -d
   docker compose ps -a
   ```

O serviço `migrate` deve terminar com código 0; web e db devem ficar saudáveis. Se houver erro, copie as últimas linhas, sem compartilhar `.env` ou senhas. O erro `pull access denied` da imagem `p4-consultores` ocorre quando a imagem local ainda não foi construída; não exige login no Docker Hub para a imagem da aplicação.

Não apague o volume do banco nem use `docker compose down -v` para resolver falhas de construção.

## Ambiente da nuvem com proxy próprio

Somente na máquina que fornece esses certificados:

```sh
P4_PROXY_CA="$CODEX_PROXY_CERT" P4_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt docker compose -f compose.yaml -f compose.cloud.yaml build
```

Isso mantém a confiança do proxy configurada sem obrigar computadores Windows a possuir caminhos de certificados Linux. Não use `--insecure`, `--trusted-host` ou `strict-ssl=false`.

## Atualização de senha e telefone

Para aplicar a senha mínima de 6 caracteres e +55 automático, baixe novamente o ZIP da branch e extraia-o. Da pasta nova, copie somente `backend` e `frontend` para a pasta atual do projeto, substituindo os arquivos correspondentes. Preserve seu `.env` e seu Dockerfile local já corrigido.

Na pasta atual, execute, aguardando cada comando terminar com sucesso:

```powershell
docker build --progress=plain -t p4-consultores:rebuild .
docker compose up --no-build --pull never -d
docker compose exec web python -m app.cli create-admin
```

No campo celular, informe DDD e número: o +55 será adicionado. Para outro país, informe + e o código correspondente. A senha pode ter somente números e precisa ter entre 6 e 200 caracteres. O comando de atualização preserva o banco; não apague volumes.
