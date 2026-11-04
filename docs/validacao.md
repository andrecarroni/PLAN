# Validação da reconstrução — 03/11/2026

Esta é a validação **da versão reconstruída**, não a reapresentação dos resultados da implementação anterior. Nenhum aluno real foi importado ou ativado. O site não foi publicado na internet.

| Verificação executada | Resultado |
| --- | --- |
| API, cálculos e preservação de configuração no PostgreSQL 17 | **52 testes passaram**, nenhum ignorado; um aviso de depreciação do cliente de testes |
| Build React/TypeScript | Passou |
| Docker | Imagem completa construída com TLS verificado; migração concluída; web e banco responderam à verificação de prontidão |
| Navegador Chromium | **13 verificações funcionais passaram**, sem erros JavaScript |
| Acessibilidade automatizada | Zero violações nas regras WCAG 2 A/AA, 2.1 AA e 2.2 AA avaliadas em planejamento, relatório, celular com letras ampliadas e administração |
| Celular | 390 × 844, inclusive com letras ampliadas, sem rolagem horizontal no planejamento |
| Desktop | 1440 × 1050; formulário e relatório funcionais |
| PDF | Download real; extração de texto confirmou R$ 1.234,56 e orientação pública, sem nota interna; PDF do teste com 8 páginas |
| Backup/restauração | Scripts `backup.sh` e `restore-check.sh` executados: dump válido e restauração em banco temporário, sem sobrescrever a aplicação |
| Configuração de produção | Compose com override validado sintaticamente com domínio fictício, sem iniciar HTTPS público |
| Configuração preservada | Teste reproduz limpeza de `.env` no checkout e restaura a mesma configuração da cópia fora do checkout; conflitos não sobrescrevem arquivos |

O comando interativo de administrador, as instruções de instalação e a verificação de prontidão são exercitados nesta entrega. O instalador preserva a configuração fora do checkout em `/workspace/shared/p4-consultores/config.env`, sem expor valores.

## Testes essenciais cobertos

- Isolamento entre alunos e rejeição de acessos não autenticados.
- Consultor e perfis acumulados com acesso a todos os alunos.
- Vendedor sem financeiro, PDF, notas ou auditoria, inclusive pela API.
- Operações administrativas exclusivas; desativação de equipe e invalidação de sessões.
- Validade anual, revogação e bloqueio com sessão já aberta; dados preservados para equipe.
- Ausência de prazo automático na sessão; validade anual não aplicada à equipe.
- Renovação com solicitação idempotente, aprovação e histórico; 29/02 tratado como 28/02 no ano seguinte.
- CSRF, senha com hash, troca/recuperação, código de uso único e limite de tentativas.
- Persistência em outra sessão, versão otimista e rejeição de requisição repetida sem duplicar itens.
- Consignados já descontados e ainda não descontados, modos de cartão, previsto/realizado, renda zero/ausente, saldo desconhecido e validação decimal.
- Projeção entre anos e limites dos meses cadastrados.
- Três correções da planilha: assinaturas incluídas, eventuais independentes de variáveis, todos os 12 meses no total anual.
- Orientações públicas e notas internas separadas, PDF protegido, publicação de conteúdos com versões.
- Prévia/importação CSV, duplicidades, cadastros pendentes, paginação e exclusão com confirmação.
- Preservação e restauração da configuração local sem trocar a senha nem sobrescrever conflitos.

## Verificações do navegador

`scripts/browser_smoke.py` verifica login real; salvamento confirmado; erro de rede mantendo o campo sem falso “Salvo”; persistência/retomada; repetição em intervalo entre anos; cópia do previsto preservando realizado; conflito entre dispositivos sem sobrescrita; valor inválido preservado; relatório com dado atual; download de PDF; celular e ampliação; revisão/publicação administrativa em banco fictício; e vendedor sem financeiro na interface e API.

Para repetir, use banco de demonstração isolado, Playwright com Chromium e a saída de `app.cli demo` em arquivo local com permissão restrita. Configure `P4_DEMO_CREDENTIALS` para esse arquivo e, opcionalmente, `P4_BASE_URL`, `P4_BROWSER_PATH` e `P4_AXE_PATH`. O script limpa o planejamento da conta fictícia e publica um conteúdo **nesse banco de demonstração**. Não execute com contas reais. Axe-core é opcional para repetir a auditoria; sem seu arquivo, o script não afirma que a acessibilidade foi verificada.

As capturas em `screenshots/` usam dados fictícios e a marca tipográfica temporária, enquanto a logo original não existir como arquivo.

## Preservação do código

Os arquivos foram incluídos em commits locais. A branch de recuperação destinada ao GitHub é `codex/p4-reconstrucao-20261103`. A entrega informa separadamente se o push e a conferência remota tiveram sucesso; um commit local sozinho não prova preservação no GitHub. O manifesto da exportação identifica o commit e os hashes do ZIP/bundle. O ZIP e bundle não incluem `.env`, banco, backups, dependências ou anexos do curso.

O novo rascunho da configuração da nuvem deve selecionar o commit reconstruído e manter instruções de instalação/inicialização correspondentes. Salvar o rascunho não publica o ambiente nem prova a restauração em uma tarefa nova. Não se deve depender apenas de arquivos não versionados dentro do checkout.

## Limites

- A validação humana com equipe/idosos continua pendente e tem roteiro próprio; auditoria automática não substitui avaliação humana completa.
- Sem rede, alterações não confirmadas ficam na memória da página. Há aviso ao sair; fechar à força ou perder o dispositivo pode perder essas alterações. Não há sincronização offline nem persistência financeira no navegador.
- Faltam arquivo original da logo, canal real de suporte, domínio/servidor público e configuração operacional de produção.
- Aprovar retenção/privacidade, backup externo agendado, revisão de segurança e teste de carga antes de alunos reais.
- Não foi validado uso simultâneo de 1.500 alunos. O override de produção foi verificado como configuração, sem obter certificado ou publicar domínio nesta tarefa.
- O container antigo `p4-postgres` foi preservado; a reconstrução usa projeto Compose e volume novos, sem remover o anterior.

### Situação do envio remoto

O push planejado foi recusado pela revisão automática antes de executar: a revisão considerou faltar autorização específica para exportar o código à branch GitHub. Não houve tentativa alternativa de contornar a decisão. Os commits e arquivos de entrega são locais; a branch remota não foi criada por esta entrega. O envio requer autorização específica do usuário. Como proteção adicional, há um restaurador local de bundle verificado que não acessa a rede nem faz reset forçado.

### Atualização: autorização e correção do Docker no Windows

Após autorização explícita do usuário, o commit da reconstrução foi enviado à branch `codex/p4-reconstrucao-20261103` e a referência remota foi conferida. A recusa descrita acima é um registro histórico, não um bloqueio atual.

O log do Windows revelou que o Dockerfile exigia `/run/secrets/ca_bundle` sem que esse secret tivesse sido montado. O Dockerfile agora seleciona certificados extras apenas quando o arquivo existe; caso contrário, usa os certificados públicos padrão, mantendo TLS habilitado. O Compose padrão não referencia arquivos de certificado Linux; a configuração de proxy da nuvem foi separada em `compose.cloud.yaml`. Foram conferidas as configurações padrão, nuvem e produção; o build completo com os certificados da nuvem passou, e a disponibilidade das raízes públicas sem secrets foi verificada em ambas as imagens-base. A execução em Windows será confirmada pelo usuário após atualizar seus arquivos; não houve teste direto em máquina Windows nesta tarefa.

### Atualização 04/11/2026: senha de 6 caracteres e Brasil como padrão

A pedido do usuário, a senha mínima passou de 12 para 6 caracteres, inclusive somente números, mantendo máximo de 200, hash scrypt e limite de tentativas. A regra é compartilhada pelo cadastro, troca, recuperação e comando de administrador e refletida na interface. Senhas existentes continuam válidas.

DDD + número, sem prefixo internacional, recebe +55 automaticamente. Número já iniciado com 55 e comprimento completo recebe somente o sinal +. Países explicitamente informados com + são preservados, e a formatação habitual (espaços, parênteses, hífen) é removida. O mesmo normalizador é usado em cadastro individual, importação CSV, login e CLI, evitando duplicidades entre versões formatadas e internacionais do mesmo número. O administrador passa a receber mensagens específicas por campo, sem mostrar a senha.

A suíte completa no PostgreSQL passou em **72 testes**, incluindo limites de senha, login/troca/recuperação com seis dígitos, criação de administrador com DDD nacional, países estrangeiros e duplicidades após normalização. A compilação React/TypeScript também passou. A aplicação instalada no Windows precisa ser reconstruída após atualizar as pastas backend/frontend.

### Edição administrativa de cadastro de aluno

Foi incluído o botão **Editar cadastro** na lista de alunos, disponível ao administrador, para alterar nome, celular e e-mail. A API exige o retrato original dos campos, bloqueia a linha ao comparar e rejeita edições simultâneas. Duplicidades de celular retornam erro sem salvamento parcial. Alterações de celular invalidam sessões e códigos de recuperação anteriores; senha, perfis, validade e financeiro são preservados. O histórico de auditoria contém autor, aluno e valores anteriores/novos desses campos.

A suíte completa passou em **85 testes** no PostgreSQL. O novo `scripts/test_profile_browser.py` usa banco descartável e verificou edição com atualização da lista, preservação dos campos após falha de rede, erro de duplicidade, cancelamento e ausência de rolagem horizontal no celular. O banco temporário é removido ao final. A compilação React/TypeScript passou. Foi corrigido também um erro no comando de geração de contas fictícias, coberto por teste de criação idempotente que preserva senhas existentes.

### Destaque das orientações no relatório

A seção “Orientações liberadas pela consultoria” foi movida para logo abaixo da identificação do aluno, antes do aviso de preenchimento e dos gráficos. O cartão usa fundo amarelo-claro, borda dourada e título escuro, com contrastes medidos acima de 8:1. A seção antiga no final foi removida. O layout foi conferido no navegador com dados fictícios em 1440 e 390 pixels, verificando posição, ausência de duplicação e de rolagem horizontal. As notas internas continuam filtradas. A compilação TypeScript/React passou; esta alteração é somente na interface do relatório.

### Equipe, conta e comercial — 04/11/2026

O cadastro administrativo da equipe foi separado do cadastro do aluno, com edição de nome/celular/e-mail, controle de conflito e auditoria. O aluno continua com o login no próprio cadastro. A conta agora separa suporte, segurança com botão de troca de senha, cadastro e histórico do acesso. As orientações ficaram compactas na tela e foram movidas para depois do nome no PDF.

O novo módulo comercial inclui dashboard, fila paginada, kanban, agenda em Brasília (45 minutos como padrão), propostas, análise por período/responsável e CSV protegido contra fórmulas. A nova autorização solicitada permite ao vendedor consultar planejamento e orientações públicas por rota dedicada, auditada e sem edição; notas internas e rotas financeiras antigas permanecem restritas. Não há capacidade de pagamento calculada automaticamente, recebimento de valores, envio de convites ou ativação automática por venda.

Validação concluída:

- **113 testes de API passaram** no PostgreSQL isolado, incluindo permissões, conflitos de versão/agenda, propostas, exportação e separação de cadastros. Há um aviso de depreciação da dependência Starlette/AnyIO.
- Compilação TypeScript/React e construção completa da imagem Docker passaram.
- `scripts/test_commercial_browser.py` concluiu 11 verificações integradas em banco descartável: equipe, segurança, fila, leitura financeira, proposta, agenda, kanban/venda, CSV, celular, histórico e PDF. Nenhum erro JavaScript foi registrado. Telas conferidas em 1440 e 390 pixels, sem rolagem horizontal na área comercial.
- Um backup da revisão anterior foi restaurado em banco temporário e atualizado de `0001` para `0002`. Todos os campos e registros das 16 tabelas anteriores foram comparados e preservados. O banco temporário foi removido.

O teste de navegador usou somente contas fictícias; não houve migração do computador Windows do usuário, publicação do site ou envio de mensagens. A atualização local está documentada em `COMERCIAL.md`. Ainda é necessária a conferência humana com a equipe e alunos, além da preparação operacional de produção descrita nas limitações anteriores.
