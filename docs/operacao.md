# Operação, produção e proteção dos dados

## Desenvolvimento versus produção

O Compose base publica web e banco somente no loopback do computador local. A API de desenvolvimento inicia com `--no-proxy-headers`. Para internet, use o override `compose.production.yaml` (Compose 2.24+): retira as portas diretas de web/banco, inicia Caddy em 80/443 e exige `P4_DOMAIN` real. Caddy obtém/renova certificados; DNS deve apontar ao servidor e as portas 80/443 precisam estar liberadas. Não se cria restrição por país.

Caddy e web têm IPs fixos na rede privada `172.30.40.0/24`; o servidor confia em cabeçalhos encaminhados somente do Caddy `172.30.40.2`. Se essa sub-rede conflitar com sua infraestrutura, ajuste a rede e o IP confiável juntos. Isso evita aceitar `X-Forwarded-For` arbitrário e permite limitar tentativas por cliente real. O banco continua apenas na rede interna de aplicação. O override força `APP_ENV=production`, ativa cookie Secure e exige PostgreSQL.

O servidor de produção deve usar instalação limpa, nova senha do banco e **nenhuma conta de demonstração**. Não reutilize os dumps ou `.env` da validação como produção. Use os comandos e conferências do guia manual. Não há implantação pública realizada por esta tarefa.

## Backup e restauração

Em Linux/macOS, com o Compose em execução:

```sh
bash scripts/backup.sh
bash scripts/restore-check.sh backups/ARQUIVO-GERADO.dump
```

O primeiro comando usa `pg_dump -Fc`, permissões restritas e verifica o catálogo do dump. O segundo cria um banco temporário com nome exclusivo, executa `pg_restore --exit-on-error`, confere contagens e versão de migração e remove somente esse banco temporário. Ele não substitui produção. Os scripts funcionam no Compose de desenvolvimento; em produção acrescente os mesmos `-f` do override aos comandos docker usados pela rotina, ou configure `COMPOSE_FILE=compose.yaml:compose.production.yaml` no Linux antes de executá-los.

No Windows, evite redirecionar um dump binário pelo PowerShell antigo. Faça a cópia sem conversão de bytes:

```powershell
New-Item -ItemType Directory -Force backups
docker compose exec db pg_dump -U p4 -d p4 -Fc -f /tmp/p4-backup.dump
docker compose cp db:/tmp/p4-backup.dump ./backups/p4-backup.dump
docker compose exec db rm /tmp/p4-backup.dump
```

O backup contém dados financeiros: restrinja acesso, criptografe pela solução corporativa e mantenha cópia fora do servidor. Agende diariamente e monitore falhas. Arquivos de backup e `.env` não são enviados ao Git nem incluídos no ZIP do código. O banco/volumes precisam de criptografia em repouso na infraestrutura; não se promete criptografia por coluna nesta aplicação.

Restauração de produção exige autorização, janela de manutenção e backup anterior. Ensaie primeiro em banco isolado, aponte uma instância isolada para ele e confira login e relatórios antes de alterar o serviço real. Não execute limpeza/restauração destrutiva diretamente em produção sem esse procedimento.

## Retenção e exclusão

Prazo definitivo de retenção precisa ser aprovado pelo controlador antes do uso real. Até essa aprovação, mantenha apenas dados fictícios nesta instância; não há expurgo automático baseado em prazo inventado. Documente finalidade, acesso e atendimento de solicitações no aviso de privacidade.

Revogação preserva os dados. Exclusão individual exige identidade/autorização verificadas, avaliação de retenção legal, motivo documentado e confirmação textual `EXCLUIR +CELULAR`. O endpoint administrativo remove cadastro, financeiro, sessões, tokens, histórico de acesso, metas e notas do aluno e seus snapshots de auditoria. Mantém somente evento mínimo de exclusão com ID, autor, motivo e instante. Notas de outros alunos escritas pela pessoa excluída são preservadas com autor nulo; não devem conter dados pessoais desnecessários no texto.

Backups imutáveis não são reescritos pela exclusão: cumpra a retenção aprovada e reaplique exclusões se restaurar backup anterior antes de liberar alunos. Não coloque dados pessoais desnecessários no motivo da exclusão. A auditoria financeira contém snapshots sensíveis; acesso somente pela equipe autorizada, com banco e backups protegidos.

## Logs e segredos

Credenciais em variáveis de ambiente/.env local, nunca no código. Cookie HttpOnly, CSRF e hash de sessão não são credenciais exibíveis à equipe. Não configure proxy ou monitoramento para registrar corpos de requisições, cookies, tokens de recuperação ou senhas. A API não registra esses valores em auditoria. O canal de recuperação ainda é administrativo controlado, sem envio externo simulado.

## Itens necessários antes de alunos reais

- Arquivo original da logo, contato de suporte e revisão administrativa dos rascunhos.
- Domínio/DNS, servidor público, HTTPS e nova instalação de produção.
- Retenção/privacidade aprovadas, backup externo agendado, monitoração e ensaio de restauração.
- Teste humano com a equipe e idosos, revisão de segurança e teste de carga.

Não foi validada concorrência de 1.500 alunos simultâneos. Paginação, índices e teste funcional não equivalem a teste de capacidade. Não há chatbot financeiro, integração bancária, conversão automática de moedas ou renovação automática.
