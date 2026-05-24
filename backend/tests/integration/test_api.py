"""
Testes de integração — chamadas HTTP reais para http://localhost:8000.
Requer o ambiente Docker rodando: docker compose up
Os testes são somente leitura e independentes de ordem.
"""
import os
import pytest
import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as c:
        yield c


@pytest.fixture(scope="module")
def first_producao(client):
    """Busca a primeira produção disponível para testes de detalhe."""
    resp = client.post("/api/search/text", json={"query": "pesquisa"})
    assert resp.status_code == 200
    resultados = resp.json()["resultados"]
    if not resultados:
        pytest.skip("Nenhuma produção no banco — rode o ETL antes dos testes de integração")
    return resultados[0]


@pytest.fixture(scope="module")
def valid_producao_id(first_producao):
    return first_producao["id"]


@pytest.fixture(scope="module")
def valid_pesquisador_id(first_producao):
    return first_producao["pesquisador"]["id"]


# ── GET /health ───────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── GET /api/stats ────────────────────────────────────────────────────────────

def test_stats_retorna_200(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200


def test_stats_campos_obrigatorios(client):
    data = client.get("/api/stats").json()
    assert "total_producoes" in data
    assert "total_pesquisadores" in data
    assert "total_vetores" in data


def test_stats_valores_positivos(client):
    data = client.get("/api/stats").json()
    assert data["total_producoes"] >= 0
    assert data["total_pesquisadores"] >= 0
    assert data["total_vetores"] >= 0


# ── GET /api/producoes/tipos ──────────────────────────────────────────────────

def test_producoes_tipos_retorna_200(client):
    resp = client.get("/api/producoes/tipos")
    assert resp.status_code == 200


def test_producoes_tipos_retorna_lista(client):
    data = client.get("/api/producoes/tipos").json()
    assert isinstance(data, list)


def test_producoes_tipos_estrutura(client):
    data = client.get("/api/producoes/tipos").json()
    if data:
        item = data[0]
        assert "tipo" in item
        assert "total" in item
        assert isinstance(item["total"], int)


# ── GET /api/producoes/{id} ───────────────────────────────────────────────────

def test_producao_detalhe_200(client, valid_producao_id):
    resp = client.get(f"/api/producoes/{valid_producao_id}")
    assert resp.status_code == 200


def test_producao_detalhe_campos(client, valid_producao_id):
    data = client.get(f"/api/producoes/{valid_producao_id}").json()
    assert "id" in data
    assert "titulo" in data
    assert "tipo_producao" in data
    assert "pesquisador" in data
    assert data["id"] == valid_producao_id


def test_producao_detalhe_sem_campos_null(client, valid_producao_id):
    data = client.get(f"/api/producoes/{valid_producao_id}").json()
    for value in data.values():
        assert value is not None, f"Campo NULL encontrado na resposta: {data}"


def test_producao_detalhe_404(client):
    resp = client.get("/api/producoes/999999999")
    assert resp.status_code == 404


# ── POST /api/search/text ─────────────────────────────────────────────────────

def test_search_text_200_com_dados(client):
    resp = client.post("/api/search/text", json={"query": "pesquisa"})
    assert resp.status_code == 200


def test_search_text_estrutura_resposta(client):
    data = client.post("/api/search/text", json={"query": "pesquisa"}).json()
    assert "total" in data
    assert "page" in data
    assert "total_pages" in data
    assert "resultados" in data
    assert isinstance(data["resultados"], list)


def test_search_text_422_query_vazia(client):
    resp = client.post("/api/search/text", json={"query": ""})
    assert resp.status_code == 422


def test_search_text_200_sem_resultados(client):
    resp = client.post(
        "/api/search/text",
        json={"query": "xyzzy_nenhum_resultado_esperado_12345_spark"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resultados"] == []
    assert data["total"] == 0


def test_search_text_paginacao(client):
    data = client.post("/api/search/text", json={"query": "pesquisa", "page": 1}).json()
    assert data["page"] == 1
    assert len(data["resultados"]) <= 20


def test_search_text_sem_campos_null_nos_cards(client):
    data = client.post("/api/search/text", json={"query": "pesquisa"}).json()
    for card in data["resultados"]:
        for value in card.values():
            assert value is not None, f"Campo NULL encontrado no card: {card}"


# ── POST /api/search/semantic ─────────────────────────────────────────────────

def test_search_semantic_200(client):
    resp = client.post("/api/search/semantic", json={"query": "aprendizado de máquina"})
    assert resp.status_code == 200


def test_search_semantic_estrutura(client):
    data = client.post("/api/search/semantic", json={"query": "aprendizado de máquina"}).json()
    assert "resultados" in data
    assert isinstance(data["resultados"], list)


def test_search_semantic_similarity_score_presente(client):
    data = client.post("/api/search/semantic", json={"query": "aprendizado de máquina"}).json()
    for item in data["resultados"]:
        assert "similarity_score" in item, f"similarity_score ausente no item: {item}"


def test_search_semantic_similarity_score_entre_0_e_1(client):
    data = client.post("/api/search/semantic", json={"query": "aprendizado de máquina"}).json()
    for item in data["resultados"]:
        score = item["similarity_score"]
        assert 0.0 <= score <= 1.0, f"similarity_score fora do intervalo [0,1]: {score}"


def test_search_semantic_422_query_vazia(client):
    resp = client.post("/api/search/semantic", json={"query": ""})
    assert resp.status_code == 422


def test_search_semantic_200_sem_resultados(client):
    resp = client.post(
        "/api/search/semantic",
        json={"query": "xyzzy_nenhum_resultado_esperado_12345_spark"}
    )
    assert resp.status_code == 200


# ── GET /api/pesquisadores/{id} ───────────────────────────────────────────────

def test_pesquisador_perfil_200(client, valid_pesquisador_id):
    resp = client.get(f"/api/pesquisadores/{valid_pesquisador_id}")
    assert resp.status_code == 200


def test_pesquisador_perfil_campos(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}").json()
    assert "id" in data
    assert "nome_completo" in data
    assert "lattes_id" in data
    assert "total_producoes" in data
    assert "indice_h" in data
    assert "total_a1_a2" in data


def test_pesquisador_perfil_sem_campos_null(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}").json()
    campos_obrigatorios = ["id", "nome_completo", "lattes_id", "total_producoes", "indice_h", "total_a1_a2"]
    for campo in campos_obrigatorios:
        assert data[campo] is not None, f"Campo obrigatório NULL: {campo}"


def test_pesquisador_perfil_404(client):
    resp = client.get("/api/pesquisadores/999999999")
    assert resp.status_code == 404


# ── GET /api/pesquisadores/{id}/producoes ─────────────────────────────────────

def test_pesquisador_producoes_200(client, valid_pesquisador_id):
    resp = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/producoes")
    assert resp.status_code == 200


def test_pesquisador_producoes_estrutura(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/producoes").json()
    assert "total" in data
    assert "page" in data
    assert "total_pages" in data
    assert "resultados" in data
    assert isinstance(data["resultados"], list)


def test_pesquisador_producoes_paginacao_maxima(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/producoes").json()
    assert len(data["resultados"]) <= 20


def test_pesquisador_producoes_404(client):
    resp = client.get("/api/pesquisadores/999999999/producoes")
    assert resp.status_code == 404


# ── GET /api/pesquisadores/{id}/stats ─────────────────────────────────────────

def test_pesquisador_stats_200(client, valid_pesquisador_id):
    resp = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/stats")
    assert resp.status_code == 200


def test_pesquisador_stats_estrutura(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/stats").json()
    assert "por_ano" in data
    assert "por_qualis" in data
    assert isinstance(data["por_ano"], list)
    assert isinstance(data["por_qualis"], list)


def test_pesquisador_stats_por_ano_campos(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/stats").json()
    for item in data["por_ano"]:
        assert "ano" in item
        assert "total" in item


def test_pesquisador_stats_por_qualis_campos(client, valid_pesquisador_id):
    data = client.get(f"/api/pesquisadores/{valid_pesquisador_id}/stats").json()
    for item in data["por_qualis"]:
        assert "qualis" in item
        assert "total" in item


def test_pesquisador_stats_404(client):
    resp = client.get("/api/pesquisadores/999999999/stats")
    assert resp.status_code == 404
