import pytest
from fastapi.testclient import TestClient

from jobfinder_api.config import Settings, get_settings
from jobfinder_api.main import create_app


@pytest.fixture
def client_with():
    """Cria um cliente da API com configurações controladas pelo teste."""

    def _make(**overrides) -> TestClient:
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **overrides)
        return TestClient(app)

    return _make


def test_health_responde_ok(client_with):
    response = client_with().get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert body["env"] == "development"


def test_health_indica_supabase_nao_configurado(client_with):
    body = client_with(supabase_url="", supabase_anon_key="").get("/health").json()

    assert body["supabase_configured"] is False


def test_health_indica_supabase_configurado_sem_vazar_chaves(client_with):
    segredo = "chave-super-secreta"
    response = client_with(
        supabase_url="https://exemplo.supabase.co",
        supabase_anon_key=segredo,
        supabase_service_role_key=segredo,
    ).get("/health")

    assert response.json()["supabase_configured"] is True
    assert segredo not in response.text


def test_rota_inexistente_retorna_404(client_with):
    assert client_with().get("/nao-existe").status_code == 404
