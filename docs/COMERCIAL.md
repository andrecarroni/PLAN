# Atualização e uso da área comercial

## Atualizar no Windows

Faça os passos na pasta atual do projeto, no PowerShell. Preserve `.env`, o Dockerfile local e o volume do banco. Não recrie as contas existentes.

1. Com o Docker Desktop aberto e o banco em execução, faça um backup:

   ```powershell
   New-Item -ItemType Directory -Force backups
   docker compose exec db pg_dump -U p4 -d p4 -Fc -f /tmp/p4-antes-comercial.dump
   docker compose cp db:/tmp/p4-antes-comercial.dump ./backups/p4-antes-comercial.dump
   Get-Item ./backups/p4-antes-comercial.dump
   ```

   Confira que o arquivo existe e guarde uma cópia fora da pasta do projeto. Se algum comando falhar, pare antes de atualizar.

2. Baixe o ZIP atualizado da branch [codex/p4-reconstrucao-20261103](https://github.com/andrecarroni/PLAN/tree/codex/p4-reconstrucao-20261103), usando **Code → Download ZIP**, e extraia em outra pasta.
3. Copie somente as pastas `backend` e `frontend` da pasta nova para a pasta atual, substituindo os arquivos. A migração nova está dentro de `backend/migrations`. Preserve `.env`, Dockerfile e `backups`.
4. Na pasta atual, execute cada comando e aguarde o sucesso antes do próximo:

   ```powershell
   docker build --progress=plain -t p4-consultores:rebuild .
   docker compose up --no-build --pull never -d db
   docker compose run --rm --no-deps migrate
   docker compose up --no-build --pull never -d
   docker compose ps -a
   ```

   A migração deve informar revisão `0002`; uma segunda execução pode não imprimir mudanças, pois já estará atualizada. `db` e `web` devem ficar saudáveis; `migrate` pode aparecer como `Exited (0)`. A migração adiciona tabelas comerciais sem remover os cadastros e planejamentos existentes.
5. Abra http://localhost:8000 e pressione **Ctrl+F5**. Entre novamente se necessário. Se houver erro, copie as últimas linhas sem enviar `.env` ou senhas. Não use `docker compose down -v`.

## Equipe, aluno e conta

- Administrador: **Administração → Equipe e perfis → Novo integrante da equipe**. Abra o integrante e use **Editar integrante** para nome, celular e e-mail. Perfis e habilitação continuam nos controles próprios.
- Aluno: cadastro e acesso ficam em **Alunos e atendimentos**. O celular é o login; +55 é automático para DDD e número brasileiros válidos. A senha inicial aceita de 6 a 200 caracteres. Números incompletos continuam sendo rejeitados.
- **Minha conta e ajuda** tem painéis separados de cadastro, suporte, segurança e histórico do acesso do aluno. **Trocar senha** abre o formulário.
- As orientações têm destaque compacto no relatório e aparecem após o nome no PDF. Notas internas continuam restritas à consultoria.

## Rotina do vendedor

1. Entre com perfil vendedor e abra **Comercial**. No dashboard, **Adicionar alunos à fila** inclui os alunos existentes que ainda não têm oportunidade. A ação é explícita e pode ser repetida sem duplicar a fila.
2. Em **Fila de consultorias**, busque o aluno e abra a consultoria. Defina responsável, etapa e próximos passos. Salve o atendimento.
3. **Consultar planejamento financeiro** apresenta dados previstos e realizados e orientações públicas, somente para leitura. A consulta é auditada. Dados incompletos não comprovam capacidade de pagamento; a decisão deve ser conversada com o aluno. Não há pontuação automática de capacidade financeira.
4. **Agendar reunião** sugere 45 minutos, com horário de Brasília. A agenda impede sobreposição de reuniões agendadas/confirmadas do mesmo responsável. O link de reunião é opcional e deve começar com `https://`. O sistema não cria chamadas nem envia convites.
5. Registre o comparecimento e avance no kanban: aguardando, agendado, consultoria, proposta, negociação, ganho ou perdido. Antes de marcar ganho, registre a condição aceita. A venda não ativa nem renova automaticamente o acesso do aluno.
6. Use **Análises e relatórios** para acompanhar o funil e baixar o CSV. Os filtros de datas têm a referência indicada na tela; o CSV exporta o funil completo e não inclui o orçamento financeiro nem as notas internas.

As referências iniciais são comunidade R$290, mentoria R$5.000 à vista ou 12 parcelas de R$497 (total R$5.964). As condições de cada proposta podem ser ajustadas. Valores de contratos são nominais, sem comprovação de recebimento, cobrança ou integração de pagamento. A equipe deve informar o custo total e negociar condições viáveis com o aluno.

Mudanças comerciais exigem salvar. Há aviso ao sair com alterações pendentes; não há agenda externa, envio de mensagens nem armazenamento offline do atendimento.
