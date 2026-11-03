# Permissões, sessões e validade

| Operação | Aluno | Consultor | Vendedor | Administrador |
| --- | --- | --- | --- | --- |
| Financeiro e PDF | Próprio, acesso ativo | Todos os alunos | Não | Todos |
| Editar planejamento | Próprio, acesso ativo | Todos os alunos | Não | Todos |
| Cadastro e situação do aluno | Próprio | Lista | Lista e pré-cadastro | Todos |
| Notas internas / atendimento | Não | Sim | Não | Sim |
| Orientações liberadas | Próprias | Consultar e registrar | Não | Consultar e registrar |
| Ativar, renovar, bloquear, revogar | Não | Não | Não | Sim |
| Gerenciar equipe e perfis | Não | Não | Não | Sim |
| Importar CSV, publicar conteúdo, suporte | Não | Não | Não | Sim |
| Solicitar renovação | Própria | Se também aluno | Se também aluno | Se também aluno |
| Auditoria por aluno | Não | Sim | Não | Sim |
| Auditoria global e exclusão | Não | Não | Não | Sim |

Perfis acumulados usam a união das permissões. Consultores acessam todos os alunos, sem carteiras. Um consultor com perfil aluno mantém os direitos de equipe independentemente do vencimento do acesso como aluno. Vendedor não obtém dados financeiros pela API nem por notas/auditoria/relatórios. A autorização não depende de esconder botões.

Login com celular E.164 (`+` e 8 a 15 dígitos), senha de 12 a 200 caracteres e e-mail opcional. Hash scrypt com sal aleatório. Sessões opacas aleatórias, só hash no banco; cookie HttpOnly e SameSite=Lax, Secure em produção. Mutações autenticadas exigem CSRF mantido em memória. Logout, troca/recuperação de senha, mudança de perfis e desativação encerram as sessões correspondentes. Senhas e tokens não são incluídos na auditoria.

**Não há expiração automática por inatividade ou duração de sessão aberta**, conforme solicitado. O cookie é de sessão do navegador, sem Max-Age/Expires; o navegador controla a retenção quando é fechado. Não há dados financeiros em localStorage/IndexedDB. O controle anual de acesso é independente da sessão.

Tentativas de login: 10 falhas por conta ou IP em 15 minutos, persistidas no banco. Contadores são inicializados por upsert e bloqueados em ordem estável no PostgreSQL. Ao implantar atrás de proxy, configure o IP confiável para distinguir clientes; não confie em cabeçalhos de qualquer origem. A API roda por padrão com `--no-proxy-headers`.

## Recuperação controlada

Não há envio externo de SMS, e-mail ou WhatsApp configurado. A tela informa isso. A equipe precisa verificar a identidade por canal previamente conhecido, nunca apenas aceitar um novo número alegado. O administrador emite um token de uso único, validade de 20 minutos, após confirmação do procedimento. O valor aparece uma vez na resposta administrativa; só hash fica no banco. Entregue por canal seguro já verificado. O usuário escolhe a nova senha na tela de recuperação. A emissão e o uso ficam auditados. Nunca solicite a senha do aluno.

## Validade anual

Instantes em UTC; referência administrativa `America/Sao_Paulo`. Ativação registra liberação e um ano de calendário de validade, mantendo a hora local. Para 29/02, o aniversário é 28/02 no ano seguinte. Renovação parte do vencimento ainda futuro; se vencido, parte da aprovação. O administrador pode definir data futura específica.

Toda operação financeira verifica estado e vencimento no servidor, inclusive com página já aberta. Expirado/bloqueado/revogado pode acessar conta, suporte e solicitar renovação; não pode consultar/editar o financeiro. Dados permanecem disponíveis à equipe autorizada. Não há renovação automática.

A equipe não tem validade anual automática. Administrador pode desativar uma conta inteira, impedindo login e encerrando sessões, e reativá-la posteriormente. Não pode remover seu próprio perfil administrativo, desativar ou excluir sua própria conta.

Revogar não exclui dados. A exclusão é separada, requer motivo documentado e confirmação textual `EXCLUIR +CELULAR`. O processo de retenção e exclusão está em `operacao.md`.
