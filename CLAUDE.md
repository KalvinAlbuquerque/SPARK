# SPARK — Claude Code Context

## Documentos obrigatórios

Antes de qualquer ação, leia:

- `SDD/constitution.md` — princípios não negociáveis do projeto
- `SDD/plan.md` — decisões técnicas e estrutura do repositório
- SDD/spec-base — guia de como criar as specs

## Regras rápidas

- Nunca calcular métricas em tempo de consulta — usar campos pré-calculados
- Toda escrita nas tabelas usa UPSERT, sem exceção
- Nenhum secret no repositório — apenas variáveis de ambiente
- Endpoints de busca retornam 200 + lista vazia, nunca 404
- Quando finalizar cada spec, renomeie o arquivo dela e complemente com _CONCLUIDA no final **IMPORTANTE**!!!!!!
- Caso tenha dúvidas sobre alguma implementação, pergunte antes de tomar qualquer decisão.

## Memory file

Use o arquivo SDD/memory.md para atualizar o andamento da implementação, esse arquivo vai ser como um context keeper para que qualquer IA possa continuar de onde você parou, assim como entender o que já foi implementado no código.

Sempre deixe o memory.md atualizado com as implementações que você fez. Toda vez que você terminar uma implementação, essa deve ir para o memory.md.

## Observações Gerais

Você tem acesso via MCP ao projeto no jira. O nome do projeto é SPARK (codigo SPK). Caso precise, você pode consultar os cartões do projeto.
