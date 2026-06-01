# Burndown Chart — Sprint 3

**Projeto:** SPARK  
**Sprint:** Sprint 3  
**Período:** 12/05/2026 a 23/05/2026 (10 dias úteis)  
**Equipe:** Kalvin Santos · Glenda Santana  
**Total de Story Points:** 32 SP

---

## Dados do Burndown

| Dia | Data | SP Restante (Real) | SP Ideal |
|---|---|---|---|
| 0 | 12/05 (Seg) | 32 | 32,0 |
| 1 | 13/05 (Ter) | 32 | 28,8 |
| 2 | 14/05 (Qua) | 27 | 25,6 |
| 3 | 15/05 (Qui) | 27 | 22,4 |
| 4 | 16/05 (Sex) | 24 | 19,2 |
| 5 | 19/05 (Seg) | 16 | 16,0 |
| 6 | 20/05 (Ter) | 8 | 12,8 |
| 7 | 21/05 (Qua) | 8 | 9,6 |
| 8 | 22/05 (Qui) | 5 | 6,4 |
| 9 | 23/05 (Sex) | 0 | 3,2 |

> **Linha ideal:** declínio linear de 32 SP (dia 0) a 0 SP (dia 9).  
> **Linha real:** trabalho aconteceu em blocos conforme as histórias foram concluídas.

---

## Gráfico (ASCII)

```
32 |*──────────────────────────── ideal
   |*  *
27 |      *  *
   |            ·
24 |               *            real
   |                  ·
19 |                     ·
16 |                        *
   |                           ·
12 |                              ·
 8 |                                 *  *
   |                                       ·
 5 |                                          *
   |                                             ·
 0 +──────────────────────────────────────────────*
   12   13   14   15   16   19   20   21   22   23
  Seg  Ter  Qua  Qui  Sex  Seg  Ter  Qua  Qui  Sex

  * = ponto real  · = linha ideal
```

---

## Log de Entregas

| Data | Issue concluída | SP entregues | Responsável |
|---|---|---|---|
| 14/05 (Qua) | SPK-91 — Schema Supabase produção | 5 SP | Kalvin Santos |
| 16/05 (Sex) | SPK-118 — Dockerfile + docker-compose | 3 SP | Glenda Santana |
| 19/05 (Seg) | SPK-92 — API FastAPI (busca + endpoints) | 8 SP | Glenda Santana |
| 20/05 (Ter) | SPK-93 — Worker embeddings + endpoints internos | 8 SP | Glenda Santana |
| 22/05 (Qui) | SPK-94 — Auth Admin + gestão de pesquisadores | 3 SP | Kalvin Santos |
| 23/05 (Sex) | SPK-95 — Deploy Railway | 5 SP | Kalvin Santos |

---

## Análise do Sprint

### Desempenho Geral

- **Velocidade planejada:** 32 SP  
- **Velocidade realizada:** 32 SP  
- **Taxa de conclusão:** 100% (6/6 histórias entregues)  

### Padrão de entrega

A equipe entregou primeiro as histórias de infraestrutura (schema, Docker) na primeira semana para desbloquear o desenvolvimento da API. As histórias de maior valor (API FastAPI, worker de embeddings) foram entregues na segunda semana.

O burndown apresenta queda em degraus — padrão típico de sprints com histórias de tamanho médio (3–8 SP) onde cada entrega representa um salto no gráfico. Não houve bloqueios nem histórias carregadas para a próxima sprint.

### Comparativo com Sprint 2

| Métrica | Sprint 2 | Sprint 3 |
|---|---|---|
| SP planejados | 27 | 32 |
| SP entregues | 27 | 32 |
| Histórias | 4 | 6 |
| Taxa de conclusão | 100% | 100% |

A equipe aumentou a velocidade em ~19% em relação à sprint anterior, reflexo das histórias bem especificadas e sem dependências externas bloqueantes.

---

## Para visualizar no Google Sheets

Copie a tabela abaixo para o Google Planilhas, selecione as três colunas e insira um gráfico de linhas (Inserir → Gráfico → Linha):

```
Dia,Real,Ideal
0,32,32
1,32,28.8
2,27,25.6
3,27,22.4
4,24,19.2
5,16,16
6,8,12.8
7,8,9.6
8,5,6.4
9,0,3.2
```

**Configuração sugerida no Planilhas:**
- Eixo X: Dia (0–9) ou Datas (12/05–23/05)
- Série 1 "Real": linha contínua, cor azul
- Série 2 "Ideal": linha tracejada, cor cinza
- Título: "Burndown — SPARK Sprint 3"
