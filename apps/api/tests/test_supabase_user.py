import json

import httpx
import pytest

from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError, SupabaseUserClient

pytestmark = pytest.mark.anyio

URL = "https://exemplo.supabase.co"


def make_client(handler) -> tuple[SupabaseUserClient, list[httpx.Request]]:
    """Cliente cujas chamadas HTTP são capturadas em vez de irem para a internet."""
    requests: list[httpx.Request] = []

    def capture(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(capture))
    return SupabaseUserClient(URL + "/", "chave-publica", "token-da-ana", http), requests


def assert_acts_as_user(request: httpx.Request) -> None:
    # Sempre o token da própria pessoa: é o que faz o RLS valer.
    assert request.headers["apikey"] == "chave-publica"
    assert request.headers["Authorization"] == "Bearer token-da-ana"


async def test_registra_consentimento_em_nome_do_usuario():
    client, requests = make_client(lambda r: httpx.Response(201, json=[{"id": "c-1"}]))

    consent_id = await client.add_consent("u-1", "analise_curriculo", "v1")

    assert consent_id == "c-1"
    [request] = requests
    assert request.method == "POST"
    assert str(request.url) == f"{URL}/rest/v1/consents"
    assert request.headers["Prefer"] == "return=representation"
    assert json.loads(request.content) == {
        "user_id": "u-1",
        "purpose": "analise_curriculo",
        "version": "v1",
    }
    assert_acts_as_user(request)


async def test_envia_arquivo_sem_sobrescrever():
    client, requests = make_client(lambda r: httpx.Response(200, json={"Key": "ok"}))

    await client.upload("u-1/abc.pdf", b"%PDF-", "application/pdf")

    [request] = requests
    assert str(request.url) == f"{URL}/storage/v1/object/curriculos/u-1/abc.pdf"
    assert request.headers["Content-Type"] == "application/pdf"
    assert request.headers["x-upsert"] == "false"
    assert request.content == b"%PDF-"
    assert_acts_as_user(request)


async def test_apaga_arquivo():
    client, requests = make_client(lambda r: httpx.Response(200, json={}))

    await client.delete_upload("u-1/abc.pdf")

    assert requests[0].method == "DELETE"
    assert str(requests[0].url) == f"{URL}/storage/v1/object/curriculos/u-1/abc.pdf"


async def test_registra_e_lista_curriculos():
    rows = [{"id": "r-1", "original_filename": "cv.pdf"}]
    client, requests = make_client(
        lambda r: httpx.Response(200 if r.method == "GET" else 201, json=rows)
    )

    assert await client.add_resume({"user_id": "u-1"}) == rows[0]
    assert await client.list_resumes() == rows

    listing = requests[1]
    assert listing.url.path == "/rest/v1/resumes"
    assert listing.url.params["order"] == "uploaded_at.desc"
    assert "storage_path" not in listing.url.params["select"]  # o caminho interno não sai da API
    assert_acts_as_user(listing)


async def test_erro_do_supabase_vira_supabase_error():
    client, _ = make_client(lambda r: httpx.Response(403, json={"message": "RLS"}))

    with pytest.raises(SupabaseError, match="HTTP 403"):
        await client.add_consent("u-1", "analise_curriculo", "v1")


async def test_falta_de_rede_vira_supabase_error():
    def offline(request):
        raise httpx.ConnectError("sem rede")

    client, _ = make_client(offline)

    with pytest.raises(SupabaseError, match="sem resposta"):
        await client.list_resumes()


async def test_busca_o_caminho_do_curriculo():
    client, requests = make_client(
        lambda r: httpx.Response(200, json=[{"storage_path": "u-1/a.pdf"}])
    )

    assert await client.get_resume_path("r-1") == "u-1/a.pdf"
    assert requests[0].url.params["id"] == "eq.r-1"
    assert_acts_as_user(requests[0])


async def test_caminho_de_curriculo_inexistente_e_none():
    client, _ = make_client(lambda r: httpx.Response(200, json=[]))

    assert await client.get_resume_path("r-1") is None


async def test_apaga_o_registro_do_curriculo():
    client, requests = make_client(lambda r: httpx.Response(204))

    await client.delete_resume("r-1")

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == "/rest/v1/resumes"
    assert requests[0].url.params["id"] == "eq.r-1"


async def test_lista_so_os_arquivos_da_pasta_da_pessoa():
    listing = [{"name": "a.pdf", "id": "x1"}, {"name": "subpasta", "id": None}]
    client, requests = make_client(lambda r: httpx.Response(200, json=listing))

    assert await client.list_files("u-1") == ["u-1/a.pdf"]
    assert str(requests[0].url) == f"{URL}/storage/v1/object/list/curriculos"
    assert json.loads(requests[0].content) == {"prefix": "u-1", "limit": 1000}
    assert_acts_as_user(requests[0])


async def test_apaga_varios_arquivos_de_uma_vez():
    client, requests = make_client(lambda r: httpx.Response(200, json=[]))

    await client.delete_files(["u-1/a.pdf", "u-1/b.pdf"])
    await client.delete_files([])  # lista vazia: nem chama o Supabase

    [request] = requests
    assert request.method == "DELETE"
    assert str(request.url) == f"{URL}/storage/v1/object/curriculos"
    assert json.loads(request.content) == {"prefixes": ["u-1/a.pdf", "u-1/b.pdf"]}


async def test_admin_apaga_a_conta_com_a_chave_secreta():
    requests: list[httpx.Request] = []

    def capture(request):
        requests.append(request)
        return httpx.Response(200, json={})

    http = httpx.AsyncClient(transport=httpx.MockTransport(capture))
    admin = SupabaseAdminClient(URL, "chave-secreta", http)

    await admin.delete_user("u-1")

    [request] = requests
    assert request.method == "DELETE"
    assert str(request.url) == f"{URL}/auth/v1/admin/users/u-1"
    assert request.headers["apikey"] == "chave-secreta"
    assert request.headers["Authorization"] == "Bearer chave-secreta"
