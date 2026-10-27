import json

import httpx
import pytest

from jobfinder_api.supabase_user import SupabaseError, SupabaseUserClient

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
