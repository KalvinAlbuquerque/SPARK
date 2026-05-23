# Proof of Work — UPSERT Pesquisadores

**Data:** 2026-05-23  
**Pipeline:** `etl/pipelines/lattes_pesquisadores.hpl`  
**Mecanismo:** `ON CONFLICT (lattes_id) DO UPDATE SET ...`

---

## Objetivo

Demonstrar que o UPSERT do pipeline ETL:

1. **Atualiza** registros existentes quando os dados do XML mudaram (não cria duplicatas)
2. **Mantém o total de linhas** — sem crescimento espúrio da tabela
3. **Registra `data_atualizacao`** — evidência de que o `DO UPDATE SET` executou

---

## Passo 1 — Estado inicial

Contagem e dados dos 3 pesquisadores alvo antes de qualquer manipulação:

```sql
SELECT id, lattes_id, nome_completo, departamento, data_atualizacao
FROM pesquisadores
WHERE lattes_id IN ('1608472474770322','1966167015825708','4436012961948689')
ORDER BY nome_completo;
```

| id | lattes_id | nome_completo | departamento | data_atualizacao |
|----|-----------|---------------|--------------|------------------|
| 50 | 1966167015825708 | Hugo Saba Pereira Cardoso | DCET | 2026-05-23 10:50:14 |
| 1 | 1608472474770322 | José Garcia Vivas Miranda | DCET | 2026-05-23 10:50:14 |
| 52 | 4436012961948689 | Maria Fernanda Rios Grassi | DCET | 2026-05-23 10:50:14 |

**Total de pesquisadores na tabela:** 8

---

## Passo 2 — Corrupção intencional dos dados

Os 3 registros foram adulterados diretamente no banco para simular dados desatualizados ou corrompidos:

```sql
UPDATE pesquisadores SET nome_completo = 'NOME CORROMPIDO 1', departamento = 'ERRADO'
WHERE lattes_id = '1608472474770322';

UPDATE pesquisadores SET nome_completo = 'NOME CORROMPIDO 2', departamento = 'ERRADO'
WHERE lattes_id = '1966167015825708';

UPDATE pesquisadores SET nome_completo = 'NOME CORROMPIDO 3', departamento = 'ERRADO'
WHERE lattes_id = '4436012961948689';
```

Estado após a corrupção:

| lattes_id | nome_completo | departamento |
|-----------|---------------|--------------|
| 1608472474770322 | NOME CORROMPIDO 1 | ERRADO |
| 1966167015825708 | NOME CORROMPIDO 2 | ERRADO |
| 4436012961948689 | NOME CORROMPIDO 3 | ERRADO |

**Total de pesquisadores na tabela:** 8 (sem alteração no count)

---

## Passo 3 — Execução do ETL

```powershell
$env:POSTGRES_PASSWORD = "spark123"
cd etl\
.\scripts\run-etl.ps1
```

Saída relevante do Hop:

```
2026/05/23 11:02:29 - UPSERT Pesquisadores.0 - Finished processing (I=0, O=0, R=8, W=8, U=0, E=0)
=== ETL concluido em 11s ===========================
```

- `R=8` — 8 linhas lidas (uma por XML)
- `W=8` — 8 linhas escritas (todas processadas pelo UPSERT)
- `E=0` — nenhum erro

---

## Passo 4 — Estado após o ETL

```sql
SELECT lattes_id, nome_completo, departamento, data_atualizacao
FROM pesquisadores
WHERE lattes_id IN ('1608472474770322','1966167015825708','4436012961948689')
ORDER BY nome_completo;

SELECT COUNT(*) AS total_pesquisadores FROM pesquisadores;
```

| lattes_id | nome_completo | departamento | data_atualizacao |
|-----------|---------------|--------------|------------------|
| 1966167015825708 | Hugo Saba Pereira Cardoso | DCET | 2026-05-23 11:02:29 |
| 1608472474770322 | José Garcia Vivas Miranda | DCET | 2026-05-23 11:02:29 |
| 4436012961948689 | Maria Fernanda Rios Grassi | DCET | 2026-05-23 11:02:29 |

**Total de pesquisadores na tabela:** 8

---

## Resultado

| lattes_id | Antes do ETL | Depois do ETL | `data_atualizacao` atualizada? |
|-----------|-------------|---------------|-------------------------------|
| 1608472474770322 | NOME CORROMPIDO 1 / ERRADO | José Garcia Vivas Miranda / DCET | Sim |
| 1966167015825708 | NOME CORROMPIDO 2 / ERRADO | Hugo Saba Pereira Cardoso / DCET | Sim |
| 4436012961948689 | NOME CORROMPIDO 3 / ERRADO | Maria Fernanda Rios Grassi / DCET | Sim |

- **Dados corrigidos** — `nome_completo` e `departamento` restaurados a partir do XML
- **Sem duplicatas** — total permaneceu 8 (não 11 ou 16)
- **`data_atualizacao` atualizado** — evidência direta de que o `DO UPDATE SET` executou (timestamp mudou de `10:50:14` para `11:02:29`)

---

## SQL do UPSERT (referência)

```sql
INSERT INTO pesquisadores
  (lattes_id, nome_completo, departamento, campus, resumo, data_atualizacao)
VALUES (?, ?, ?, ?, ?, NOW())
ON CONFLICT (lattes_id) DO UPDATE SET
  nome_completo    = EXCLUDED.nome_completo,
  departamento     = EXCLUDED.departamento,
  campus           = EXCLUDED.campus,
  resumo           = EXCLUDED.resumo,
  data_atualizacao = NOW();
```

A chave de conflito é `lattes_id` — definida como `UNIQUE CONSTRAINT` na tabela `pesquisadores`.
