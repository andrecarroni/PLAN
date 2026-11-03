# Validação guiada da P4 Consultores

Atualizado em 03/11/2026: a reconstrução está disponível e os testes automatizados constam em `validacao.md`. Os cenários deste roteiro são para execução humana pela equipe e permanecem não executados até o preenchimento das evidências.

## Preparação

- Usar o commit da reconstrução identificado na entrega e seguir PASSO-A-PASSO.md. A reconstrução é uma nova implementação validada, não uma recuperação byte a byte da versão anterior.
- Usar exclusivamente banco e contas fictícias, separados de produção: dois alunos, um consultor, um vendedor, um administrador e uma conta com consultor + vendedor.
- Gerar senhas individuais; não registrar senhas, tokens ou dados reais nas evidências.
- Escolher uma pessoa da equipe para testar no computador e outra no celular. Incluir uma pessoa com pouca familiaridade tecnológica, sem importar dados reais.
- Registrar versão/commit, navegador, tamanho de tela, responsável e data da execução. Usar os estados passou, falhou, bloqueado e não executado.

## Sessão de teste sugerida: 45 a 60 minutos

| Perfil / cenário | Ação | Resultado esperado | Estado nesta instância |
| --- | --- | --- | --- |
| Aluno: entrada | Entrar com celular internacional e senha; usar mostrar/ocultar senha | Login real e mensagem compreensível em caso de erro | Não executado pela equipe |
| Aluno: preenchimento | Informar renda líquida fictícia de R$ 3.000 e despesa fixa de R$ 1.000 | Campos legíveis, teclado numérico, valores em reais | Não executado pela equipe |
| Salvamento automático | Alterar um valor e aguardar a confirmação; recarregar depois | “Salvando” seguido de “Salvo” somente após resposta do servidor; valor persistido | Não executado pela equipe |
| Perda de conexão | Desconectar a rede durante uma alteração; reconectar e tentar novamente | Aviso de falha, valor mantido na página e nenhum falso “Salvo” | Não executado pela equipe |
| Sessão aberta | Manter a página aberta durante a sessão de validação | Sem encerramento por inatividade; um teste de 60 minutos não prova ausência de um prazo maior | Não executado pela equipe |
| Outro dispositivo | Entrar na mesma conta em outro navegador e consultar dados já salvos | Dados recuperados do servidor | Não executado pela equipe |
| Edição simultânea | Abrir dois navegadores; salvar no primeiro e tentar salvar uma edição antiga no segundo | Conflito explícito, sem sobrescrita silenciosa | Não executado pela equipe |
| Consignado | Cadastrar R$ 300 como já descontados da renda líquida | Com a renda e despesa do exemplo, sobra de R$ 2.000; consignado não é subtraído novamente | Não executado pela equipe |
| Cartão | Registrar a mesma compra por categoria e na fatura, identificando os modos | Apenas o modo escolhido entra no orçamento; usuário é orientado a evitar duplicidade | Não executado pela equipe |
| Renda zero/ausente | Comparar mês com zero e mês sem renda informada | Percentual indisponível com explicação; nulo não apresentado como zero | Não executado pela equipe |
| Doze meses | Selecionar novembro como início e repetir uma despesa somente entre dezembro e fevereiro | Período atravessa o ano; repetição respeita limites | Não executado pela equipe |
| Previsto e realizado | Informar R$ 1.000 previsto e R$ 900 realizado para a mesma despesa | Relatórios mantêm as séries separadas | Não executado pela equipe |
| Relatório/PDF | Abrir relatório e baixar PDF do mesmo período e série | Mesmos cálculos, pendências identificadas, sem notas internas | Não executado pela equipe |
| Isolamento entre alunos | Tentar consultar o segundo aluno pela interface e diretamente pela API | Acesso negado pelo servidor | Não executado pela equipe |
| Consultor | Abrir os dois alunos, editar dados e registrar uma nota interna e uma orientação pública | Acesso a todos os alunos; apenas orientação pública chega ao aluno/PDF | Não executado pela equipe |
| Vendedor | Consultar cadastro, fazer pré-cadastro e tentar abrir dados financeiros pela API | Cadastro permitido, conta pendente, dados financeiros negados | Não executado pela equipe |
| Perfis acumulados | Acessar com consultor + vendedor | União das permissões, sem poderes administrativos | Não executado pela equipe |
| Administrador | Ativar, revogar e renovar acesso fictício; consultar histórico | Autor e datas registrados; sem renovação automática | Não executado pela equipe |
| Validade anual | Vencer/revogar o acesso do aluno com sua página já aberta | Operações financeiras bloqueadas; dados preservados e renovação disponível | Não executado pela equipe |
| Importação CSV | Fazer prévia com celular repetido; corrigir e confirmar lote fictício | Duplicidade identificada; confirmação explícita; importação não ativa contas | Não executado pela equipe |
| Conteúdo do curso | Revisar rascunho e publicar uma versão no banco fictício | Rascunho não aparece ao aluno; publicação registra aprovação e versão | Não executado pela equipe |
| Recuperação de acesso | Testar o procedimento administrativo com canal verificado | Token temporário de uso único; nenhum envio externo fictício anunciado | Não executado pela equipe |
| Acessibilidade | Usar teclado, ampliar letras e preencher no celular | Foco visível, rótulos, alvos de toque confortáveis e ausência de rolagem horizontal | Não executado pela equipe |

A validade anual administrativa permanece independente do tempo da sessão aberta. Esta validação não deve remover esse controle.

## Registro de problema

Copie uma ficha para cada ocorrência:

- Identificador do cenário:
- Responsável e data:
- Versão/commit:
- Perfil fictício utilizado (sem senha):
- Navegador/dispositivo:
- Passos para reproduzir:
- Resultado esperado:
- Resultado observado:
- Evidência sem informações sensíveis:
- Impacto: impede uso, afeta cálculo/permissão/salvamento ou dificulta compreensão:
- Correção e resultado do novo teste:

## Critérios para iniciar um piloto

Todos os cenários de autorização, cálculos, persistência, conflito e confidencialidade devem passar. Resolver problemas que impeçam o uso por idosos. Confirmar logo original, contato real de suporte, revisão dos conteúdos, domínio/HTTPS, política de retenção e backup com restauração ensaiada antes de usar dados reais. Não tratar teste automatizado de acessibilidade como avaliação humana completa nem prometer capacidade simultânea de 1.500 alunos sem teste de carga.

A liberação do piloto e a publicação pública são etapas posteriores, com decisão explícita. Nenhum aluno real deve ser ativado durante esta preparação.
