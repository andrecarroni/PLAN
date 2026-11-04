# P4 Consultores — o que fazer manualmente

O código foi reconstruído porque o checkout restaurado tinha apenas o README inicial. A nova versão usa commits Git e será entregue também como ZIP e Git bundle, sem senhas nem dados financeiros. A cópia do código não substitui o backup do banco.

## 1. Guarde uma cópia fora deste chat

1. Baixe `p4-consultores-codigo.zip` e `p4-consultores-historico.bundle` pelos links da entrega.
2. Guarde-os no computador e em outro local de sua confiança. O ZIP serve para abrir os arquivos; o bundle preserva os commits.
3. O envio foi autorizado e confirmado na branch **codex/p4-reconstrucao-20261103**. No GitHub, selecione essa branch, clique em **Code → Download ZIP** e extraia o arquivo. Para guardar o histórico, use `git clone --branch codex/p4-reconstrucao-20261103 https://github.com/andrecarroni/PLAN.git`.
4. Se o GitHub ainda não tiver a branch, extraia o ZIP e faça upload dos arquivos/pastas na interface do seu repositório. Não envie `.env`, backups ou senhas. Com Git instalado, o bundle também pode ser clonado: `git clone p4-consultores-historico.bundle PLAN`; o checkout será o commit exportado.
5. Nas configurações deste ambiente, revise e salve as instruções novas. O instalador inclui também uma restauração local a partir do bundle verificado, guardado fora do checkout. Publique o **ambiente** somente depois de guardar uma cópia externa dos arquivos. Isso não publica o site, e a restauração em uma nova tarefa ainda precisará ser conferida.

## 2. Abra no seu computador para validar

1. Instale **Docker Desktop** (Windows/macOS) ou Docker Engine com Compose (Linux). Para o modo de produção fornecido, use Compose 2.24 ou mais recente.
2. Instale **Python 3**. No Windows, habilite o launcher `py` durante a instalação. Python será usado apenas para gerar uma senha aleatória na configuração inicial; as dependências da aplicação são instaladas no Docker.
3. Extraia o ZIP. Abra um terminal na pasta que contém `compose.yaml` e `README.md`.
4. Gere a configuração local:

   ```sh
   python3 scripts/configure.py
   ```

   No Windows, use `py scripts/configure.py`. O comando cria `.env` com senha aleatória e preserva um arquivo existente. **Não envie esse arquivo para ninguém nem para o GitHub.**

5. Inicie a aplicação:

   ```sh
   docker compose up --build -d
   docker compose ps
   ```

   Aguarde banco saudável, migração concluída e web saudável. O serviço `migrate` deve terminar com código 0; isso é esperado.

6. No navegador **desse mesmo computador**, digite `http://localhost:8000`. Esse endereço não abre o servidor desta conversa a partir de outro computador.
7. Crie seu administrador:

   ```sh
   docker compose exec web python -m app.cli create-admin
   ```

   Informe nome, celular com DDD (+55 é acrescentado automaticamente para Brasil), e uma senha de 6 a 200 caracteres. Para outro país, informe `+` e o código internacional. A senha não aparece enquanto você digita. Não existe senha padrão de produção.

8. Prepare os conteúdos em rascunho:

   ```sh
   docker compose exec web python -m app.cli seed-course
   ```

9. Entre com seu celular e senha. Abra **Administração → Suporte** e informe o contato real da equipe.
10. Para parar sem excluir dados, use `docker compose stop`. Para iniciar novamente, use `docker compose up -d`. **Não use `down -v`**, porque esse comando apaga o volume do banco.

## 3. Faça a validação com dados fictícios

1. Use uma instalação/banco separado da produção. Não importe sua base real agora.
2. Você pode criar contas fictícias na Administração ou gerar a demonstração:

   ```sh
   docker compose exec -e ALLOW_DEMO=1 web python -m app.cli demo
   ```

   As senhas aleatórias aparecem uma vez no seu terminal. O comando não funciona com `APP_ENV=production`.
3. Tenha dois alunos, um consultor e um vendedor fictícios. Teste também uma conta com mais de um perfil.
4. Use `docs/roteiro-validacao-equipe.md`. Inclua alguém com pouca familiaridade com tecnologia e teste pelo celular.
5. Confira preenchimento, salvamento automático, interrupção de conexão, retomada, relatórios e PDF. Teste permissões também pela API com apoio técnico.
6. Em **Administração → Conteúdos**, revise texto, aula e referência antes de publicar cada rascunho. Não publique orientações jurídicas/bancárias sem validação atualizada.
7. Não coloque esse banco de demonstração em produção. A ativação de alunos reais ocorre em instalação limpa, depois da aprovação do piloto.

## 4. Inclua sua logo original

1. Obtenha a imagem original em PNG, preservando desenho, texto e proporções. A imagem inserida na conversa não está disponível como arquivo nos anexos restaurados.
2. Salve uma cópia em `frontend/public/logo.png`. Não a redesenhe e não corte o texto original.
3. Recrie a aplicação:

   ```sh
   docker compose up --build -d
   ```

4. Confira a logo na tela e no PDF. No Docker, o mesmo arquivo compilado é usado pelos dois. Fora do Docker, `LOGO_PATH` permite selecionar o arquivo no servidor.
5. Salve essa inclusão no Git e atualize sua cópia de segurança do código.

## 5. Coloque o site na internet, após a validação

Esta etapa precisa de informações que não estão disponíveis neste chat: um servidor contratado, acesso a ele e um domínio sob seu controle. Não compre serviços nem compartilhe senhas em chat para isso.

1. Contrate/prepare um servidor Linux público com Docker e Compose 2.24+. Deixe portas 80 e 443 disponíveis. Proteja o acesso administrativo do servidor.
2. Copie a versão do código validada para o servidor. Não copie o `.env` nem o banco da demonstração. Use a logo original já incluída.
3. Gere um `.env` **novo** com `python3 scripts/configure.py` no servidor. Abra o arquivo localmente e acrescente uma linha `P4_DOMAIN=planejamento.seudominio.com.br`, substituindo pelo domínio que você controla.
4. No painel DNS do domínio, crie um registro A para o IPv4 do servidor. Crie AAAA somente se o IPv6 estiver configurado e acessível. Aguarde a propagação.
5. Inicie com HTTPS e portas diretas de banco/web removidas:

   ```sh
   docker compose -f compose.yaml -f compose.production.yaml up --build -d
   docker compose -f compose.yaml -f compose.production.yaml ps
   ```

   O Caddy obtém o certificado para o domínio real. A rede privada `172.30.40.0/24` precisa estar livre no servidor. Veja `operacao.md` se houver conflito.

6. Abra `https://SEU-DOMINIO` no navegador e confira o certificado válido. Não libere alunos se o navegador acusar problema de HTTPS.
7. Crie o administrador e os rascunhos na instalação limpa:

   ```sh
   docker compose -f compose.yaml -f compose.production.yaml exec web python -m app.cli create-admin
   docker compose -f compose.yaml -f compose.production.yaml exec web python -m app.cli seed-course
   ```

8. Configure suporte, contas da equipe e conteúdos aprovados. Não execute `demo` em produção.
9. Com apoio do responsável técnico, agende backup externo criptografado e ensaie a restauração. Aprove política de privacidade e retenção. Os comandos estão em `operacao.md`.
10. Faça um piloto pequeno com liberação administrativa explícita. Só depois importe os demais alunos por CSV com prévia e ative os acessos aprovados. Não há ativação ou renovação automática.

## 6. Como não perder o código novamente

Depois de uma alteração aprovada, registre os arquivos em commit e envie para o seu repositório remoto. Não inclua `.env`, banco ou dependências. A branch reconstruída tem commits locais e uma exportação independente; a validação da entrega informa se o envio remoto funcionou. Para gerar novas cópias do código versionado:

```sh
python3 scripts/archive.py
```

O ZIP e o bundle são gerados na pasta `p4-entrega` ao lado do projeto. Somente arquivos já incluídos no commit entram na exportação. Faça também backup do banco, separadamente; ele contém os cadastros e planejamentos.

### Restauração local se aparecer somente o README inicial

O bundle e o manifesto ficam em `/workspace/p4-entrega`. Uma cópia do restaurador fica em `/workspace/shared/p4-consultores/restore-source.sh`. As instruções salvas da nuvem usam esse restaurador quando o código está ausente. Ele verifica SHA-256, exige o commit inicial conhecido e usa Git sem força; havendo alterações ou colisões, interrompe para preservar o trabalho. O procedimento foi ensaiado em checkout descartável, sem modificar o checkout principal. Ainda é necessário conferir a preservação desses arquivos após publicar uma nova versão do ambiente.

## Se a construção falhar no Windows

Para `failed to execute bake` ou `invalid path: /run/secrets/ca_bundle`, siga [WINDOWS-DOCKER.md](WINDOWS-DOCKER.md). A correção mantém certificados padrão no computador local e certificados extras opcionais na nuvem. Não precisa reinstalar o Docker nem apagar dados.

## Editar o cadastro de um aluno

1. Entre como administrador e abra **Alunos e atendimentos**.
2. Busque o aluno e clique em **Editar cadastro**, na linha dele.
3. O formulário será aberto acima da lista. Altere nome, celular com DDD ou e-mail e clique em **Salvar alterações**.
4. Aguarde a mensagem de sucesso. Se houver erro de conexão, os campos permanecem na tela para tentar novamente. Celular já utilizado por outra pessoa é rejeitado; uma edição simultânea também é rejeitada.
5. Se mudar o celular, informe ao aluno que deve entrar novamente usando o novo número; a senha permanece a mesma.

Para instalar essa melhoria na versão Windows já em uso, baixe o ZIP atualizado da branch e copie somente as pastas `backend` e `frontend` sobre as correspondentes da instalação atual, substituindo os arquivos. Preserve `.env` e o Dockerfile local. Execute `docker build --progress=plain -t p4-consultores:rebuild .`, aguarde sucesso e depois `docker compose up --no-build --pull never -d`. Atualize a página do navegador. A atualização não exige criar contas novamente nem modificar o banco.
