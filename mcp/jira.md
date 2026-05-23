### Conectando Claude Code ao MCP do Jira

Pacote usado: [`jira-mcp`](https://www.npmjs.com/package/jira-mcp) via npm (servidor stdio local).

---

#### Passo 1: Instale o pacote

```bash
mkdir -p ~/.config/jira-mcp
cd ~/.config/jira-mcp
npm init -y
npm install jira-mcp
```

O `index.js` ficará em `~/.config/jira-mcp/node_modules/jira-mcp/index.js`.

---

#### Passo 2: Crie um API Token no Atlassian

Acesse [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens), clique em **Create API token**, dê um nome e copie o token gerado.

---

#### Passo 3: Adicione o servidor MCP ao projeto

No Claude Code, edite `~/.claude.json` (ou use `/mcp` → Add server) e adicione na seção `mcpServers` do projeto:

```json
{
  "jira": {
    "type": "stdio",
    "command": "node",
    "args": ["C:\\Users\\<usuario>\\.config\\jira-mcp\\node_modules\\jira-mcp\\index.js"],
    "env": {
      "JIRA_INSTANCE_URL": "https://sua-empresa.atlassian.net",
      "JIRA_USER_EMAIL": "seu-email@gmail.com",
      "JIRA_API_KEY": "seu-api-token",
      "JIRA_DEFAULT_PROJECT": "PROJ"
    }
  }
}
```

**Atenção — nomes corretos das variáveis de ambiente:**

| Correto | Errado (não funciona) |
|---|---|
| `JIRA_INSTANCE_URL` | `JIRA_HOST` |
| `JIRA_USER_EMAIL` | `JIRA_EMAIL` |
| `JIRA_API_KEY` | `JIRA_API_TOKEN` |

---

#### Passo 4: Reinicie o Claude Code

Feche e reabra. Verifique com `/mcp` — o servidor `jira` deve aparecer como `✓ connected`.

---

#### Usando na prática

```
> Busque o ticket SPK-13
> Liste os tickets abertos do projeto SPK
> Qual o status do SPK-12?
```

As ferramentas disponíveis são `get_issue` e `jql_search`.
