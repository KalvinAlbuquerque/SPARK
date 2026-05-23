### Conectando Claude Code ao MCP do Jira

A abordagem oficial e mais estável é usar o **Atlassian Rovo MCP Server** com autenticação por API token.

O endpoint SSE mais antigo (OAuth) está sendo descontinuado após 30 de junho de 2026, então o uso de API token é o método recomendado para workflows no terminal. [Builder.io](https://www.builder.io/blog/claude-code-with-jira)

---

#### Passo 1: Instale o Claude Code

bash

```bash
npminstall -g @anthropic-ai/claude-code
claude --version
```

---

#### Passo 2: Crie um API Token no Atlassian

Acesse [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens), clique em  **Create API token** , dê um nome (ex: "Claude Code MCP") e copie o token gerado imediatamente, pois ele não aparecerá novamente. [Builder.io](https://www.builder.io/blog/claude-code-with-jira)

Depois, codifique suas credenciais em base64:

bash

```bash
echo -n "seu-email@empresa.com:seu-api-token"| base64
```

Salve o output, ele será usado na configuração.

---

#### Passo 3: Configure o MCP no Claude Code

Crie ou edite o arquivo de configuração:

**Mac/Linux:** `~/.config/claude/mcp.json`
**Windows:** `C:\Users\[usuario]\AppData\Roaming\Claude\mcp.json`

Conteúdo do arquivo:

json

```json
{
"mcpServers":{
"jira":{
"command":"node",
"args":["/caminho/absoluto/para/mcp-jira-server/dist/index.js"],
"env":{
"JIRA_HOST":"https://sua-empresa.atlassian.net",
"JIRA_EMAIL":"seu-email@empresa.com",
"JIRA_API_TOKEN":"seu-api-token",
"JIRA_DEFAULT_PROJECT":"PROJ"
}
}
}
}
```

---

#### Alternativa via CLI

Você pode adicionar o servidor diretamente pelo terminal com o comando `claude mcp add --transport stdio jira -- node $HOME/.config/jira-mcp/index.js`. [GitHub](https://github.com/rui-branco/jira-mcp)

---

#### Usando na prática

Com o MCP configurado, você pode usar linguagem natural dentro do Claude Code:

```
> Busque o ticket PROJ-123
> Crie uma tarefa de bug com prioridade alta sobre o problema de login
> Liste meus tickets abertos atribuídos a mim
```

O MCP traduz seus prompts em chamadas estruturadas para a API do Jira, permitindo criar issues, atualizar tickets, gerenciar sprints e muito mais diretamente do terminal. [Composio](https://composio.dev/content/jira-mcp-server)
