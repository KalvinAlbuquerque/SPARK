# Burndown Chart — Sprint Extra

**Projeto:** SPARK  
**Sprint:** Sprint Extra  
**Período:** 01/06/2026 a 03/06/2026 (3 dias úteis)  
**Equipe:** Kalvin Santos · Glenda Santana  
**Total de Story Points:** 8 SP

---

## Dados do Burndown

| Dia | Data | SP Restante (Real) | SP Ideal |
|---|---|---|---|
| 0 | 01/06 (Seg) | 8 | 8,0 |
| 1 | 01/06 (fim do dia) | 3 | 5,3 |
| 2 | 02/06 (Ter) | 3 | 2,7 |
| 3 | 03/06 (Qua) | 0 | 0,0 |

> SPK-119 (3 SP) e SPK-120 (2 SP) foram entregues no dia 01/06 — burndown acelerado no primeiro dia.  
> SPK-14 (3 SP) entregue no dia 03/06.

---

## Gráfico (ASCII)

```
 8 |*
   | ·
 5 |    ·
   |
 3 |       *──────────
   |                  ·
   |
 0 +────────────────────*
   01/06    02/06    03/06
   Seg      Ter      Qua

   * = ponto real  · = linha ideal
```

---

## Log de Entregas

| Data | Issue concluída | SP entregues | Responsável |
|---|---|---|---|
| 01/06 (Seg) | SPK-119 — Geração de capa por IA | 3 SP | Kalvin Santos |
| 01/06 (Seg) | SPK-120 — Proxy foto pesquisador Lattes | 2 SP | Kalvin Santos |
| 03/06 (Qua) | SPK-14 — Spike modelos de embedding | 3 SP | Glenda Santana |

---

## Análise do Sprint

### Desempenho Geral

- **Velocidade planejada:** 8 SP  
- **Velocidade realizada:** 8 SP  
- **Taxa de conclusão:** 100% (3/3 histórias entregues)

### Padrão de entrega

O burndown apresenta queda acentuada no primeiro dia — SPK-119 e SPK-120 foram desenvolvidas em paralelo por Kalvin Santos no dia 01/06, aproveitando que ambas envolvem Next.js Route Handlers com pattern similar. O SPK-14 (spike de pesquisa) ficou para os dias seguintes por ser trabalho de análise independente de desenvolvimento.

### Comparativo com Sprints anteriores

| Métrica | Sprint 3 | Sprint Extra |
|---|---|---|
| SP planejados | 32 | 8 |
| SP entregues | 32 | 8 |
| Taxa de conclusão | 100% | 100% |
| Duração | 10 dias | 3 dias |

---

## Para visualizar no Google Sheets

```
Dia,Real,Ideal
0,8,8
1,3,5.3
2,3,2.7
3,0,0
```

**Configuração sugerida:**
- Eixo X: Dia (0–3) ou Datas (01/06–03/06)
- Série "Real": linha contínua, cor azul
- Série "Ideal": linha tracejada, cor cinza
- Título: "Burndown — SPARK Sprint Extra"
