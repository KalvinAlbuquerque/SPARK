## Proof of Work

**Data de execução:** 2026-05-23w

### Estado antes do ETL

Todos os campos zerados (estado inicial):

```
          nome_completo          | total_producoes | total_a1_a2 | indice_h
---------------------------------+-----------------+-------------+----------
 Aloisio Santos Nascimento Filho |               0 |           0 |        0
 Eduardo Manuel de Freitas Jorge |               0 |           0 |        0
 Hugo Saba Pereira Cardoso       |               0 |           0 |        0
 José Garcia Vivas Miranda       |               0 |           0 |        0
 Maria Fernanda Rios Grassi      |               0 |           0 |        0
 Mayara Maria de Jesus Almeida   |               0 |           0 |        0
 Paulo Jorge Silveira Ferreira   |               0 |           0 |        0
 Raphael Silva do Rosário        |               0 |           0 |        0
```

### Resultado após 1ª execução (ETL completo — 122s)

```
          nome_completo          | total_producoes | total_a1_a2 | indice_h
---------------------------------+-----------------+-------------+----------
 Aloisio Santos Nascimento Filho |              74 |          13 |        3
 Eduardo Manuel de Freitas Jorge |              68 |           5 |        2
 Hugo Saba Pereira Cardoso       |              91 |          13 |        4
 José Garcia Vivas Miranda       |             127 |          45 |        6
 Maria Fernanda Rios Grassi      |              70 |          19 |        4
 Mayara Maria de Jesus Almeida   |              16 |           3 |        0
 Paulo Jorge Silveira Ferreira   |               0 |           0 |        0
 Raphael Silva do Rosário        |              16 |           6 |        2
```

### Resultado após 2ª execução (idempotência — 117s)

Valores idênticos — idempotência confirmada ✓

### Log do pipeline `metricas_pesquisadores`

```
Listar Pesquisadores.0  - Finished processing (I=8, O=0, R=0, W=8, U=0, E=0)
Atualizar Metricas.0    - Finished processing (I=0, O=0, R=8, W=8, U=0, E=0)
metricas_pesquisadores  - Pipeline duration : 0.167 seconds
```

**Observações:**

- `R=8` — 8 pesquisadores selecionados pela janela `data_atualizacao >= NOW() - INTERVAL '2 hours'`
- `W=8, E=0` — 8 UPDATEs executados sem erros SQL
- Paulo Jorge Silveira Ferreira: `total_producoes=0, total_a1_a2=0, indice_h=0` — correto (sem produções no XML)
- Mayara Maria de Jesus Almeida: `indice_h=0` — correto (produções sem JCR suficiente para h≥1)
- José Garcia Vivas Miranda: `indice_h=6` — maior índice H do conjunto (127 produções, 45 A1/A2)
- O `Log Erro Metrica` receber as 8 linhas é o quirk cosmético do `distribute=N` em copy mode (já documentado no memory.md) — `E=0` confirma que não houve erro real
