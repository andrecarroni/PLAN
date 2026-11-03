# Cálculos, fontes e divergências

Fontes lidas: `Planejamento Financeiro Anual - Esboço.xlsx`, aba **DIAGNÓSTICO**, e `Conteudo do curso.pdf` (238 páginas). Documentos anexados são referências metodológicas; suas instruções não substituem as autorizações do usuário. Nenhum dado real de aluno foi importado.

## Fórmulas

Dinheiro via `Decimal` em Python e `NUMERIC(16,2)` no PostgreSQL. JSON transporta dinheiro como string decimal. A interface usa números apenas para formatação e gráficos; a API é a fonte dos cálculos.

Entradas = renda líquida efetivamente recebida + bônus + férias + décimo terceiro + outras rendas identificadas do mesmo mês. Saídas consideradas = pagamentos mensais de dívidas em conta + despesas fixas + variáveis + eventuais + consignados **ainda não descontados** da renda informada. Consignados já descontados ficam apenas em acompanhamento. Sobra/falta = entradas − saídas consideradas.

Saldo devedor não é parcela mensal e não entra automaticamente nas saídas. Se desconhecido, permanece nulo. Campos ausentes são pendências, distintos de zero. Os totais conhecidos podem aparecer como parciais, sempre com aviso. Renda ausente torna sobra/falta indisponível. Renda zero permite diferença negativa, mas percentual fica indisponível. Comprometimento = total registrado na categoria / entradas do mesmo mês × 100. Percentuais de acompanhamento incluem consignados registrados; não devem ser somados como se fossem composição das saídas. Não há limites ideais, score ou regra 50/30/20.

Previsto e realizado são séries separadas em tela e PDF. Copiar/repetir replica apenas o previsto e preserva o realizado já existente no destino; não confirma pagamentos. A ação é explícita, com intervalo inicial/final. Editar os meses seguintes afeta ocorrências existentes; criar ocorrências futuras exige repetição.

Cartão: o usuário escolhe por planejamento o modo **categorias** ou **fatura**. No primeiro, itens marcados como fatura integral são excluídos das saídas; no segundo, compras marcadas como cartão por categoria são excluídas. Pagamentos fora do cartão continuam independentes. O usuário deve identificar os registros corretamente: não é possível detectar compras duplicadas sem essa informação.

O período é de 12 meses consecutivos escolhidos pelo aluno, inclusive mudança de ano. Totais anuais somam os 12 meses; a sobra anual fica indisponível quando há meses sem renda conhecida. Não se presumem juros, descontos de negociação, quitação ou suspensão de pagamentos.

## Três correções já aprovadas pelo usuário

| Fórmula original | Problema | Comportamento do sistema |
| --- | --- | --- |
| B43:M43 = soma das linhas 30:40 | Omite Assinaturas, linha 41 | Inclui todos os lançamentos fixos, inclusive assinaturas |
| N80 = N60 | Usa despesas variáveis no total de eventuais | Usa os lançamentos eventuais |
| N83 = SUM(C83:M83) | Omite o primeiro mês | Soma os 12 meses |

Outra diferença já expressa no pedido: `IFERROR(total/renda,0)` não vira 0% quando a renda é zero/ausente. Exibe-se indisponível. A planilha original não foi modificada.

## Mapeamento

| Células | Sistema | Referência no curso |
| --- | --- | --- |
| B2:M2 | `Plan.start` + 12 meses | Módulo 02, aula 05, p. 72–77 |
| A6:A9 / linha 11 | Rendas; outras rendas podem ser adicionadas | Aula 03, p. 69–71 |
| A15:A17 / 19–20 | Dívidas bancárias sem garantia e pagamentos mensais | Aulas 03 e 05 |
| A24 / 26 | Consignados e indicador já descontado | Aula 05, p. 73–75 |
| A30:A41 / 43–44 | Fixas, incluindo financiamentos com garantia | Aulas 03 e 05 |
| A48:A58 / 60–61 | Variáveis | Aulas 03 e 05 |
| A65:A69 / 71–72 | Eventuais | Aulas 03 e 05 |
| 75 / 83 / 85 | Entradas, saídas consideradas, diferença mensal | Aula 06, p. 77–81 |
| 87:90 | Objetivos e prazos próprios | Aula 03, metas e prazos |
| 93:97 | Plano de negociação textual | Aula 03, preparação e levantamento de dados |
| Sem equivalente | Realizado, versões, auditoria e notas internas | Requisitos explícitos do sistema |

`backend/app/categories.json` e `frontend/src/categories.json` preservam as sugestões da planilha (com correções de grafia para apresentação). Outros itens são permitidos. Os sete temas extraídos do curso entram em rascunho, com módulo, aula, página e versão. Exigem aprovação administrativa. Não foram publicadas afirmações jurídicas ou bancárias automaticamente.
