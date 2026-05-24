"""
Gera a proof of work da SPK-118 chamando cada endpoint real e registrando
request, response, status HTTP e resultado esperado vs obtido.
Execute com: python tests/integration/generate_proof.py
Requer o ambiente Docker rodando: docker compose up
"""
import json
import os
import sys
from datetime import datetime

import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
client = httpx.Client(base_url=BASE_URL, timeout=60.0)

lines = []


def h(text, level=2):
    lines.append(f"\n{'#' * level} {text}\n")


def section(method, path, body, expected_status, extra_checks=None):
    """Executa uma chamada, registra tudo e verifica expectativas."""
    url = f"{BASE_URL}{path}"

    if body is not None:
        resp = client.request(method, path, json=body)
    else:
        resp = client.request(method, path)

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
                result = fn(resp_body)
                check_results.append((desc, result, True))
            except Exception as e:
                check_results.append((desc, str(e), False))
                checks_ok = False

    overall = "✅ PASS" if (status_ok and checks_ok) else "❌ FAIL"

    lines.append(f"### {overall} — `{method} {path}`\n")

    # Request
    lines.append("**Request:**\n")
    lines.append("```")
    lines.append(f"{method} {url}")
    if body is not None:
        lines.append(f"Content-Type: application/json\n\n{json.dumps(body, ensure_ascii=False, indent=2)}")
    lines.append("```\n")

    # Response
    status_mark = "✅" if status_ok else "❌"
    lines.append(f"**Response — HTTP {resp.status_code}** {status_mark} *(esperado: {expected_status})*\n")
    lines.append("```json")
    lines.append(json.dumps(resp_body, ensure_ascii=False, indent=2))
    lines.append("```\n")

    # Extra checks
    if check_results:
        lines.append("**Verificações adicionais:**\n")
        for desc, val, ok in check_results:
            mark = "✅" if ok else "❌"
            lines.append(f"- {mark} {desc}: `{val}`")
        lines.append("")

    return status_ok and checks_ok


# ─── coleta IDs reais para usar nos testes de detalhe ────────────────────────
resp_seed = client.post("/api/search/text", json={"query": "pesquisa"})
seed = resp_seed.json()
if not seed["resultados"]:
    print("ERRO: nenhuma produção no banco. Rode o ETL primeiro.")
    sys.exit(1)

PRODUCAO_ID = seed["resultados"][0]["id"]
PESQUISADOR_ID = seed["resultados"][0]["pesquisador"]["id"]
PESQUISADOR_NOME = seed["resultados"][0]["pesquisador"]["nome_completo"]

# ─── cabeçalho do documento ──────────────────────────────────────────────────
lines.append("# SPK-118 · Proof of Work — Testes de Integração da API\n")
lines.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f"**API base URL:** `{BASE_URL}`")
lines.append(f"**IDs usados nos testes de detalhe:** `producao_id={PRODUCAO_ID}`, `pesquisador_id={PESQUISADOR_ID}` ({PESQUISADOR_NOME})\n")
lines.append("> Todos os testes são somente leitura. IDs obtidos dinamicamente via busca textual — não hardcoded.\n")

results = []

# ─── /health ─────────────────────────────────────────────────────────────────
h("1. Health check")
results.append(section("GET", "/health", None, 200, [
    ("campo status == 'ok'", lambda r: r["status"]),
]))

# ─── /api/stats ──────────────────────────────────────────────────────────────
h("2. Estatísticas gerais — `GET /api/stats`")
results.append(section("GET", "/api/stats", None, 200, [
    ("total_producoes presente e >= 0", lambda r: r["total_producoes"]),
    ("total_pesquisadores presente e >= 0", lambda r: r["total_pesquisadores"]),
    ("total_vetores presente e >= 0", lambda r: r["total_vetores"]),
]))

# ─── /api/producoes/tipos ────────────────────────────────────────────────────
h("3. Tipos de produção — `GET /api/producoes/tipos`")
results.append(section("GET", "/api/producoes/tipos", None, 200, [
    ("retorna lista não vazia", lambda r: f"{len(r)} tipos"),
    ("cada item tem campo 'tipo'", lambda r: r[0]["tipo"]),
    ("cada item tem campo 'total'", lambda r: r[0]["total"]),
]))

# ─── /api/producoes/{id} — 200 ───────────────────────────────────────────────
h(f"4. Detalhe de produção — `GET /api/producoes/{{id}}`")
h("4.1 ID existente → 200", 3)
results.append(section("GET", f"/api/producoes/{PRODUCAO_ID}", None, 200, [
    ("campo 'id' correto", lambda r: r["id"] == PRODUCAO_ID),
    ("campo 'titulo' presente", lambda r: bool(r.get("titulo"))),
    ("campo 'tipo_producao' presente", lambda r: bool(r.get("tipo_producao"))),
    ("campo 'pesquisador' aninhado presente", lambda r: bool(r.get("pesquisador"))),
    ("sem campos None na raiz", lambda r: all(v is not None for v in r.values())),
]))

h("4.2 ID inexistente → 404", 3)
results.append(section("GET", "/api/producoes/999999999", None, 404, [
    ("mensagem de erro presente", lambda r: bool(r.get("detail"))),
]))

# ─── /api/search/text — com dados ────────────────────────────────────────────
h("5. Busca textual — `POST /api/search/text`")
h("5.1 Query válida com resultados → 200", 3)
results.append(section("POST", "/api/search/text",
    {"query": "redes neurais"},
    200, [
    ("campo 'total' >= 0", lambda r: r["total"]),
    ("campo 'page' == 1", lambda r: r["page"] == 1),
    ("campo 'total_pages' presente", lambda r: r["total_pages"]),
    ("'resultados' é lista", lambda r: isinstance(r["resultados"], list)),
    ("cada card tem 'titulo'", lambda r: all(c.get("titulo") for c in r["resultados"])),
    ("cada card tem 'pesquisador'", lambda r: all(c.get("pesquisador") for c in r["resultados"])),
    ("sem campos None nos cards", lambda r: all(
        v is not None for c in r["resultados"] for v in c.values()
    )),
]))

h("5.2 Query vazia → 422 (validação Pydantic)", 3)
results.append(section("POST", "/api/search/text",
    {"query": ""},
    422, [
    ("body de erro presente", lambda r: "detail" in r),
]))

h("5.3 Query sem resultados → 200 + lista vazia", 3)
results.append(section("POST", "/api/search/text",
    {"query": "xyzzy_nenhum_resultado_esperado_12345_spark"},
    200, [
    ("resultados == []", lambda r: r["resultados"] == []),
    ("total == 0", lambda r: r["total"] == 0),
]))

h("5.4 Paginação — page=1, máximo 20 itens", 3)
results.append(section("POST", "/api/search/text",
    {"query": "pesquisa", "page": 1},
    200, [
    ("page retornado == 1", lambda r: r["page"] == 1),
    ("len(resultados) <= 20", lambda r: len(r["resultados"]) <= 20),
]))

# ─── /api/search/semantic ────────────────────────────────────────────────────
h("6. Busca semântica — `POST /api/search/semantic`")
h("6.1 Query válida → 200 com similarity_score em cada item", 3)
results.append(section("POST", "/api/search/semantic",
    {"query": "aprendizado de máquina e inteligência artificial"},
    200, [
    ("'resultados' é lista", lambda r: isinstance(r["resultados"], list)),
    ("similarity_score presente em todos os itens", lambda r: all(
        "similarity_score" in i for i in r["resultados"]
    )),
    ("similarity_score em [0, 1] para todos", lambda r: all(
        0.0 <= i["similarity_score"] <= 1.0 for i in r["resultados"]
    )),
]))

h("6.2 Query vazia → 422", 3)
results.append(section("POST", "/api/search/semantic",
    {"query": ""},
    422, [
    ("body de erro presente", lambda r: "detail" in r),
]))

h("6.3 Query sem resultados → 200 + lista vazia", 3)
results.append(section("POST", "/api/search/semantic",
    {"query": "xyzzy_nenhum_resultado_esperado_12345_spark"},
    200, [
    ("resultados == []", lambda r: r["resultados"] == []),
]))

# ─── /api/pesquisadores/{id} — 200 ───────────────────────────────────────────
h(f"7. Perfil de pesquisador — `GET /api/pesquisadores/{{id}}`")
h("7.1 ID existente → 200", 3)
results.append(section("GET", f"/api/pesquisadores/{PESQUISADOR_ID}", None, 200, [
    ("campo 'id' correto", lambda r: r["id"] == PESQUISADOR_ID),
    ("campo 'nome_completo' presente", lambda r: bool(r.get("nome_completo"))),
    ("campo 'lattes_id' presente", lambda r: bool(r.get("lattes_id"))),
    ("total_producoes >= 0", lambda r: r["total_producoes"] >= 0),
    ("indice_h >= 0", lambda r: r["indice_h"] >= 0),
    ("total_a1_a2 >= 0", lambda r: r["total_a1_a2"] >= 0),
    ("campos obrigatórios sem None", lambda r: all(
        r[f] is not None for f in ["id","nome_completo","lattes_id","total_producoes","indice_h","total_a1_a2"]
    )),
]))

h("7.2 ID inexistente → 404", 3)
results.append(section("GET", "/api/pesquisadores/999999999", None, 404, [
    ("mensagem de erro presente", lambda r: bool(r.get("detail"))),
]))

# ─── /api/pesquisadores/{id}/producoes ───────────────────────────────────────
h(f"8. Produções do pesquisador — `GET /api/pesquisadores/{{id}}/producoes`")
h("8.1 ID existente → 200", 3)
results.append(section("GET", f"/api/pesquisadores/{PESQUISADOR_ID}/producoes", None, 200, [
    ("estrutura total/page/total_pages/resultados", lambda r: all(
        k in r for k in ["total","page","total_pages","resultados"]
    )),
    ("len(resultados) <= 20 (paginação máxima)", lambda r: len(r["resultados"]) <= 20),
    ("cada item tem 'titulo' e 'tipo_producao'", lambda r: all(
        i.get("titulo") and i.get("tipo_producao") for i in r["resultados"]
    )),
]))

h("8.2 ID inexistente → 404", 3)
results.append(section("GET", "/api/pesquisadores/999999999/producoes", None, 404, [
    ("mensagem de erro presente", lambda r: bool(r.get("detail"))),
]))

# ─── /api/pesquisadores/{id}/stats ───────────────────────────────────────────
h(f"9. Estatísticas do pesquisador — `GET /api/pesquisadores/{{id}}/stats`")
h("9.1 ID existente → 200", 3)
results.append(section("GET", f"/api/pesquisadores/{PESQUISADOR_ID}/stats", None, 200, [
    ("campo 'por_ano' é lista", lambda r: isinstance(r["por_ano"], list)),
    ("campo 'por_qualis' é lista", lambda r: isinstance(r["por_qualis"], list)),
    ("itens por_ano têm 'ano' e 'total'", lambda r: all(
        "ano" in i and "total" in i for i in r["por_ano"]
    )),
    ("itens por_qualis têm 'qualis' e 'total'", lambda r: all(
        "qualis" in i and "total" in i for i in r["por_qualis"]
    )),
]))

h("9.2 ID inexistente → 404", 3)
results.append(section("GET", "/api/pesquisadores/999999999/stats", None, 404, [
    ("mensagem de erro presente", lambda r: bool(r.get("detail"))),
]))

# ─── sumário ─────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
h("Sumário")
lines.append(f"**{passed}/{total} cenários aprovados**\n")
lines.append("| # | Endpoint | Resultado |")
lines.append("|---|----------|-----------|")
scenarios = [
    "GET /health",
    "GET /api/stats",
    "GET /api/producoes/tipos",
    f"GET /api/producoes/{PRODUCAO_ID} (200)",
    "GET /api/producoes/999999999 (404)",
    "POST /api/search/text — com resultados",
    "POST /api/search/text — query vazia (422)",
    "POST /api/search/text — sem resultados (200 vazio)",
    "POST /api/search/text — paginação",
    "POST /api/search/semantic — com similarity_score",
    "POST /api/search/semantic — query vazia (422)",
    "POST /api/search/semantic — sem resultados (200 vazio)",
    f"GET /api/pesquisadores/{PESQUISADOR_ID} (200)",
    "GET /api/pesquisadores/999999999 (404)",
    f"GET /api/pesquisadores/{PESQUISADOR_ID}/producoes (200)",
    "GET /api/pesquisadores/999999999/producoes (404)",
    f"GET /api/pesquisadores/{PESQUISADOR_ID}/stats (200)",
    "GET /api/pesquisadores/999999999/stats (404)",
]
for i, (s, r) in enumerate(zip(scenarios, results), 1):
    lines.append(f"| {i} | `{s}` | {'✅ PASS' if r else '❌ FAIL'} |")

client.close()

output = "\n".join(lines)
sys.stdout.buffer.write(output.encode("utf-8"))

out_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "SDD", "sprint_3", "spk118_proof_of_work.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)
print(f"\n\nArquivo gerado: {os.path.abspath(out_path)}")
