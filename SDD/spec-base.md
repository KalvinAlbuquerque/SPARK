Aqui está a base conceitual consolidada, direto da fonte oficial do spec-kit:

---

### O que é uma `spec.md` no SDD

Uma especificação é a fonte de verdade do projeto. Ela descreve **quem** vai usar o sistema, **o que** o problema resolve, **por que** importa, **como os usuários vão interagir** com ele, e  **como é o sucesso** . Pense nisso como um contrato entre você e o agente de IA sobre o que está sendo construído. [github](https://roelantd.github.io/spec-kit-workshop/03-specify-phase)

---


### O que DEVE estar na spec

| Categoria                       | Exemplos                                                               |
| ------------------------------- | ---------------------------------------------------------------------- |
| **Usuários**             | "Desenvolvedores que trabalham em múltiplos projetos"                 |
| **Problemas**             | "Perder o controle de tarefas e prioridades diárias"                  |
| **Jornadas do usuário**  | "Usuário abre o app, vê as tarefas de hoje ordenadas por prioridade" |
| **Funcionalidades**       | "Capacidade de marcar tarefas como concluídas"                        |
| **Critérios de sucesso** | "Usuários completam 20% mais tarefas por semana"                      |
| **Experiências**         | "O app parece responsivo e rápido de usar"                            |
| **Restrições**          | "Deve funcionar offline"                                               |
| **User Stories**          | "Como desenvolvedor, quero capturar ideias rapidamente..."             |

 [github](https://roelantd.github.io/spec-kit-workshop/03-specify-phase)

---

### O que NÃO deve estar na spec

| Categoria            | Por que não               | Vai onde |
| -------------------- | -------------------------- | -------- |
| "Use React"          | Decisão tecnológica      | Plan     |
| "REST API com JWT"   | Detalhe de implementação | Plan     |
| "PostgreSQL"         | Decisão de stack          | Plan     |
| "Singleton pattern"  | Arquitetura de código     | Plan     |
| "Express middleware" | Escolha de biblioteca      | Plan     |

 [github](https://roelantd.github.io/spec-kit-workshop/03-specify-phase)

---

### As 9 seções da spec

1. **Overview** — descrição de alto nível em 2 a 3 frases
2. **Target Users** — quem vai usar; seja específico sobre os tipos de usuário
3. **Problem Statement** — qual dor ou necessidade isso endereça
4. **User Journeys** — cenários passo a passo mostrando como o usuário interage com o sistema
5. **Core Features** — quais capacidades o sistema deve prover
6. **Success Metrics** — como mediremos se isso teve sucesso
7. **Constraints** — quais limitações existem (orçamento, tempo, plataforma)
8. **Assumptions** — o que estamos tomando como dado
9. **Out of Scope** — o que explicitamente NÃO estamos construindo

 [github](https://roelantd.github.io/spec-kit-workshop/03-specify-phase)

---

### Os sinais de alerta clássicos

**Muito técnico:**
`❌ "O sistema usará JWT tokens para autenticação"`
`✅ "Usuários permanecem logados entre sessões"`

**Muito vago:**
`❌ "O app deve ser rápido"`
`✅ "Comandos executam em menos de 100ms; atualizações da UI parecem instantâneas"`

**Focado em implementação:**
`❌ "Usar React hooks para gerenciamento de estado"`
`✅ "A aplicação lembra as preferências do usuário entre sessões"`

**Falta contexto de usuário:**
`❌ "Adicionar operações CRUD"`
`✅ "Usuários podem criar, visualizar, atualizar e deletar suas tarefas"`

 [github](https://roelantd.github.io/spec-kit-workshop/03-specify-phase)

---

### Nível de detalhe ideal

Detalhado o suficiente para que alguém pudesse construir algo similar sem fazer perguntas de esclarecimento. Mas não tão detalhado que se torne um manual técnico. **Regra prática:** se você se pegar falando sobre padrões de código ou bibliotecas específicas, foi longe demais. [github](https://roelantd.github.io/spec-kit-workshop/03-specify-phase)

---

### Checklist de validação antes de passar para o `plan.md`

* O problema está claro: um estranho entenderia o que está sendo resolvido
* Os usuários são específicos: consigo nomear pessoas reais que se encaixam nas personas
* As jornadas são completas: casos de uso principais e casos extremos cobertos
* As funcionalidades são focadas no usuário: descrevem o que o usuário  **faz** , não como é construído
* O sucesso é mensurável: podemos determinar objetivamente se funcionou
* O escopo está delimitado: seções claras de "dentro" e "fora do escopo"
* Sem decisões técnicas: nenhuma menção a tecnologias, frameworks ou padrões específicos
* Premissas documentadas: o que estamos tomando como dado está explícito
* Restrições listadas: limitações e fronteiras identificadas

Adicione no final um prompt bem construído instruindo ao claude code ler o spec e desenvolver a tarefa autonomamente.
