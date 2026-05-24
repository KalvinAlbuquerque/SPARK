"""
Gera a proof of work da SPK-93 chamando cada endpoint interno real e registrando
request, response, status HTTP e resultado esperado vs obtido.

Execute com:
  python tests/integration/generate_proof_spk93.py

Requer:
  - Ambiente Docker rodando: docker compose up
  - Variável de ambiente INTERNAL_API_KEY configurada (ou passada via argumento)
    Exemplo: INTERNAL_API_KEY=minha-chave python tests/integration/generate_proof_spk93.py
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_KEY = os.getenv("INTERNAL_API_KEY", "")

if not API_KEY:
    print("ERRO: variável INTERNAL_API_KEY não definida.")
    print("  Uso: INTERNAL_API_KEY=<chave> python tests/integration/generate_proof_spk93.py")
    sys.exit(1)

AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

client = httpx.Client(base_url=BASE_URL, timeout=300.0)
lines: list[str] = []

# ─── helpers ─────────────────────────────────────────────────────────────────

def h(text, level=2):
    lines.append(f"\n{'#' * level} {text}\n")


def _call(method, path, *, json_body=None, files=None, headers=None):
    kw: dict = {}
    if headers:
        kw["headers"] = headers
    if json_body is not None:
        kw["json"] = json_body
    if files is not None:
        kw["files"] = files
    return client.request(method, path, **kw)


def section(title, method, path, expected_status, extra_checks=None,
            json_body=None, files=None, headers=None, request_label=None):
    resp = _call(method, path, json_body=json_body, files=files, headers=headers)

    try:
        resp_body = resp.json()
    except Exception:
        resp_body = resp.text

    status_ok = resp.status_code == expected_status
    checks_ok = True
    check_results = []

    if extra_checks:
        for desc, fn in extra_checks:
            try:
                val = fn(resp_body)
                check_results.append((desc, val, True))
            except Exception as e:
                check_results.append((desc, str(e), False))
                checks_ok = False

    overall = "✅ PASS" if (status_ok and checks_ok) else "❌ FAIL"
    lines.append(f"### {overall} — `{method} {path}`\n")
    if title:
        lines.append(f"*{title}*\n")

    # Request
    lines.append("**Request:**\n")
    lines.append("```")
    display_headers = dict(headers or {})
    if "Authorization" in display_headers:
        display_headers["Authorization"] = "Bearer <INTERNAL_API_KEY>"
    req_line = f"{method} {BASE_URL}{path}"
    for k, v in display_headers.items():
        req_line += f"\n{k}: {v}"
    if request_label:
        req_line += f"\n\n{request_label}"
    elif json_body is not None:
        req_line += f"\nContent-Type: application/json\n\n{json.dumps(json_body, ensure_ascii=False, indent=2)}"
    lines.append(req_line)
    lines.append("```\n")

    # Response
    status_mark = "✅" if status_ok else "❌"
    lines.append(f"**Response — HTTP {resp.status_code}** {status_mark} *(esperado: {expected_status})*\n")
    lines.append("```json")
    if isinstance(resp_body, str):
        lines.append(resp_body[:2000])
    else:
        lines.append(json.dumps(resp_body, ensure_ascii=False, indent=2)[:3000])
    lines.append("```\n")

    if check_results:
        lines.append("**Verificações adicionais:**\n")
        for desc, val, ok in check_results:
            mark = "✅" if ok else "❌"
            lines.append(f"- {mark} {desc}: `{val}`")
        lines.append("")

    return status_ok and checks_ok, resp_body


# ─── cabeçalho ───────────────────────────────────────────────────────────────

lines.append("# SPK-93 · Proof of Work — Worker de Embeddings e Endpoints Internos\n")
lines.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f"**API base URL:** `{BASE_URL}`\n")
lines.append("> Endpoints internos exigem `Authorization: Bearer <INTERNAL_API_KEY>`. Chave omitida nos logs por segurança.\n")

results = []
CREATED_ID: int | None = None

# ─── 1. Autenticação — sem token ──────────────────────────────────────────────
h("1. Autenticação — acesso sem token retorna 403")

ok, _ = section(
    "Nenhum header de autorização enviado",
    "GET", "/internal/pesquisadores", 403,
    extra_checks=[
        ("campo 'detail' presente", lambda r: bool(r.get("detail"))),
    ],
)
results.append(ok)

ok, _ = section(
    "Token errado (não coincide com INTERNAL_API_KEY)",
    "POST", "/internal/trigger-embeddings", 403,
    headers={"Authorization": "Bearer token-invalido"},
    extra_checks=[
        ("campo 'detail' presente", lambda r: bool(r.get("detail"))),
    ],
)
results.append(ok)

# ─── 2. GET /internal/pesquisadores ──────────────────────────────────────────
h("2. Listar pesquisadores — `GET /internal/pesquisadores`")

ok, list_resp = section(
    "Com autenticação válida — retorna lista de pesquisadores",
    "GET", "/internal/pesquisadores", 200,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("campo 'total' >= 0", lambda r: r["total"] >= 0),
        ("campo 'resultados' é lista", lambda r: isinstance(r["resultados"], list)),
        ("cada item tem lattes_id", lambda r: all("lattes_id" in i for i in r["resultados"])),
        ("cada item tem total_producoes", lambda r: all("total_producoes" in i for i in r["resultados"])),
    ],
)
results.append(ok)

h("2.1 Filtro por nome — `GET /internal/pesquisadores?q=Hugo`", 3)
ok, _ = section(
    "Filtro por nome parcial (case-insensitive)",
    "GET", "/internal/pesquisadores?q=Hugo", 200,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("resultados contêm 'Hugo' no nome", lambda r: all(
            "hugo" in i["nome_completo"].lower() for i in r["resultados"]
        ) if r["resultados"] else True),
    ],
)
results.append(ok)

# ─── 3. POST /internal/pesquisadores ─────────────────────────────────────────
h("3. Criar pesquisador — `POST /internal/pesquisadores`")

NOVO_PESQUISADOR = {
    "lattes_id": "0000000000000001",
    "nome_completo": "Pesquisador Teste SPK-93",
    "departamento": "DCET",
    "campus": "Campus I",
}

ok, create_resp = section(
    "UPSERT — cria novo pesquisador, retorna 201",
    "POST", "/internal/pesquisadores", 201,
    json_body=NOVO_PESQUISADOR,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("campo 'id' presente", lambda r: isinstance(r.get("id"), int)),
        ("nome_completo correto", lambda r: r["nome_completo"] == "Pesquisador Teste SPK-93"),
        ("lattes_id correto", lambda r: r["lattes_id"] == "0000000000000001"),
        ("departamento correto", lambda r: r["departamento"] == "DCET"),
    ],
)
results.append(ok)

if ok and isinstance(create_resp, dict):
    CREATED_ID = create_resp.get("id")

h("3.1 Idempotência — mesmo lattes_id faz UPDATE (não duplica)", 3)
NOVO_PESQUISADOR_V2 = {**NOVO_PESQUISADOR, "nome_completo": "Pesquisador Teste SPK-93 v2"}
ok, upsert_resp = section(
    "Segundo POST com mesmo lattes_id atualiza o nome — 201",
    "POST", "/internal/pesquisadores", 201,
    json_body=NOVO_PESQUISADOR_V2,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("id igual ao criado anteriormente", lambda r: r.get("id") == CREATED_ID),
        ("nome atualizado para v2", lambda r: r["nome_completo"] == "Pesquisador Teste SPK-93 v2"),
    ],
)
results.append(ok)

# ─── 4. DELETE /internal/pesquisadores/{id} ───────────────────────────────────
h("4. Deletar pesquisador — `DELETE /internal/pesquisadores/{id}`")

if CREATED_ID:
    ok, _ = section(
        f"Delete do pesquisador criado no passo 3 (id={CREATED_ID}) → 204",
        "DELETE", f"/internal/pesquisadores/{CREATED_ID}", 204,
        headers=AUTH_HEADERS,
    )
    results.append(ok)

    h("4.1 Confirmar deleção — pesquisador não aparece mais na listagem", 3)
    ok, after_del = section(
        "Após deleção, filtro por lattes_id não retorna o pesquisador",
        "GET", "/internal/pesquisadores?q=Teste+SPK-93", 200,
        headers=AUTH_HEADERS,
        extra_checks=[
            ("resultados não contêm pesquisador deletado", lambda r: all(
                i.get("lattes_id") != "0000000000000001" for i in r["resultados"]
            )),
        ],
    )
    results.append(ok)

h("4.2 Delete de ID inexistente → 404", 3)
ok, _ = section(
    "Pesquisador que não existe retorna 404",
    "DELETE", "/internal/pesquisadores/999999999", 404,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("campo 'detail' presente", lambda r: bool(r.get("detail"))),
    ],
)
results.append(ok)

# ─── 5. POST /internal/trigger-embeddings ─────────────────────────────────────
h("5. Acionar worker de embeddings — `POST /internal/trigger-embeddings`")

ok, embed_resp = section(
    "Gera embeddings das produções pendentes — retorna vetores_gerados",
    "POST", "/internal/trigger-embeddings", 200,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("campo 'vetores_gerados' presente", lambda r: "vetores_gerados" in r),
        ("vetores_gerados é inteiro >= 0", lambda r: isinstance(r["vetores_gerados"], int) and r["vetores_gerados"] >= 0),
    ],
)
results.append(ok)

if ok and isinstance(embed_resp, dict):
    vetores = embed_resp.get("vetores_gerados", 0)
    h("5.1 Idempotência — segunda chamada gera 0 vetores (ON CONFLICT DO NOTHING)", 3)
    ok2, embed_resp2 = section(
        "Segunda chamada imediata — todas as produções já têm vetor",
        "POST", "/internal/trigger-embeddings", 200,
        headers=AUTH_HEADERS,
        extra_checks=[
            ("vetores_gerados == 0 (já existem)", lambda r: r["vetores_gerados"] == 0),
        ],
    )
    results.append(ok2)

# ─── 6. POST /internal/trigger-etl ────────────────────────────────────────────
h("6. Trigger ETL via upload XML — `POST /internal/trigger-etl`")

h("6.1 Sem arquivos → 422 (validação)", 3)
ok, _ = section(
    "Request sem files retorna 422",
    "POST", "/internal/trigger-etl", 422,
    headers=AUTH_HEADERS,
    extra_checks=[
        ("campo 'detail' presente", lambda r: "detail" in r),
    ],
)
results.append(ok)

h("6.2 Com um XML Lattes real → executa pipeline completo", 3)
XML_PATH = Path(__file__).parent.parent.parent.parent / "data" / "xml" / "4940207771377721.xml"
if XML_PATH.exists():
    with open(XML_PATH, "rb") as f:
        xml_bytes = f.read()

    ok, etl_resp = section(
        f"Upload de {XML_PATH.name} — executa 7 fases (extração → embeddings)",
        "POST", "/internal/trigger-etl", 200,
        files=[("files", (XML_PATH.name, xml_bytes, "text/xml"))],
        headers=AUTH_HEADERS,
        request_label=f"multipart/form-data\nfiles[0]: {XML_PATH.name} ({len(xml_bytes):,} bytes)",
        extra_checks=[
            ("campo 'pesquisadores' presente", lambda r: "pesquisadores" in r),
            ("campo 'producoes' presente", lambda r: "producoes" in r),
            ("campo 'qualis_match' presente", lambda r: "qualis_match" in r),
            ("campo 'vetores_gerados' presente", lambda r: "vetores_gerados" in r),
            ("campo 'erros' é lista", lambda r: isinstance(r.get("erros"), list)),
            ("pesquisadores >= 1 (pelo menos 1 UPSERT)", lambda r: r["pesquisadores"] >= 1),
        ],
    )
    results.append(ok)
else:
    lines.append(f"> ⚠️ Arquivo `{XML_PATH}` não encontrado — cenário 6.2 pulado.\n")

# ─── 7. Busca semântica com vetores reais ─────────────────────────────────────
h("7. Busca semântica — `POST /api/search/semantic` com vetores reais")

ok, sem_resp = section(
    "Query sobre dengue/epidemiologia — tema presente nos XMLs carregados",
    "POST", "/api/search/semantic",
    200,
    json_body={"query": "epidemiologia de doenças infecciosas dengue arbovirose"},
    extra_checks=[
        ("'resultados' é lista", lambda r: isinstance(r["resultados"], list)),
        ("retornou pelo menos 1 resultado (vetores existem)", lambda r: len(r["resultados"]) > 0),
        ("cada item tem similarity_score", lambda r: all(
            "similarity_score" in i for i in r["resultados"]
        )),
        ("similarity_score em [0, 1]", lambda r: all(
            0.0 <= i["similarity_score"] <= 1.0 for i in r["resultados"]
        )),
        ("resultado mais relevante tem score >= 0.5", lambda r: r["resultados"][0]["similarity_score"] >= 0.5),
        ("cada item tem titulo e pesquisador", lambda r: all(
            i.get("titulo") and i.get("pesquisador") for i in r["resultados"]
        )),
    ],
)
results.append(ok)

h("7.1 Ranqueamento — query diferente retorna resultados distintos no topo", 3)
ok, sem_resp2 = section(
    "Query sobre redes neurais/aprendizado — deve ranquear diferente da anterior",
    "POST", "/api/search/semantic",
    200,
    json_body={"query": "redes neurais aprendizado de máquina inteligência artificial"},
    extra_checks=[
        ("retornou pelo menos 1 resultado", lambda r: len(r["resultados"]) > 0),
        ("título do top-1 diferente do top-1 da busca por dengue", lambda r: (
            r["resultados"][0]["titulo"] != sem_resp.get("resultados", [{}])[0].get("titulo", "")
            if sem_resp.get("resultados") else True
        )),
        ("similarity_score do top-1 >= 0.4", lambda r: r["resultados"][0]["similarity_score"] >= 0.4),
    ],
)
results.append(ok)

# ─── Confirmação via /api/stats ───────────────────────────────────────────────
h("8. Confirmação — `GET /api/stats` mostra vetores gerados")

ok, stats_resp = section(
    "total_vetores > 0 após trigger-embeddings",
    "GET", "/api/stats", 200,
    extra_checks=[
        ("total_vetores > 0 (worker gerou vetores)", lambda r: r["total_vetores"] > 0),
        ("total_producoes > 0", lambda r: r["total_producoes"] > 0),
        ("total_pesquisadores > 0", lambda r: r["total_pesquisadores"] > 0),
    ],
)
results.append(ok)

# ─── sumário ──────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
h("Sumário")
lines.append(f"**{passed}/{total} cenários aprovados**\n")
lines.append("| # | Cenário | Resultado |")
lines.append("|---|---------|-----------|")

scenarios = [
    "GET /internal/pesquisadores — sem token → 403",
    "POST /internal/trigger-embeddings — token errado → 403",
    "GET /internal/pesquisadores — com token → 200",
    "GET /internal/pesquisadores?q=Hugo — filtro por nome",
    "POST /internal/pesquisadores — criar (201)",
    "POST /internal/pesquisadores — UPSERT idempotente (201)",
    f"DELETE /internal/pesquisadores/{CREATED_ID or '?'} — 204",
    "GET /internal/pesquisadores?q= — confirmar deleção",
    "DELETE /internal/pesquisadores/999999999 — 404",
    "POST /internal/trigger-embeddings — gera vetores",
    "POST /internal/trigger-embeddings — idempotência (0 gerados)",
    "POST /internal/trigger-etl — sem arquivos → 422",
    "POST /internal/trigger-etl — com XML → pipeline completo",
    "POST /api/search/semantic — dengue/epidemiologia com vetores reais",
    "POST /api/search/semantic — redes neurais (ranqueamento diferente)",
    "GET /api/stats — total_vetores > 0",
]

for i, (s, r) in enumerate(zip(scenarios, results), 1):
    lines.append(f"| {i} | `{s}` | {'✅ PASS' if r else '❌ FAIL'} |")

client.close()

# ─── gravar arquivo ───────────────────────────────────────────────────────────
output = "\n".join(lines)
sys.stdout.buffer.write(output.encode("utf-8"))
sys.stdout.buffer.write(b"\n")

out_path = (
    Path(__file__).parent.parent.parent.parent
    / "SDD" / "sprint_3" / "spk93_proof_of_work.md"
)
out_path.write_text(output, encoding="utf-8")
print(f"\n\nArquivo gerado: {out_path.resolve()}", file=sys.stderr)
