import io
import zipfile

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from jobfinder_api.auth import CurrentUser, UserSession, get_token_verifier
from jobfinder_api.config import Settings
from jobfinder_api.main import create_app
from jobfinder_api.resumes import (
    DOCX,
    MAX_BYTES,
    PDF,
    clean_filename,
    detect_content_type,
    get_resume_store,
)
from jobfinder_api.supabase_user import SupabaseUserClient
from tests.conftest import USER_ID

PDF_BYTES = b"%PDF-1.7\n conteudo do curriculo"


def docx_bytes(extra: dict[str, str] | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in (extra or {"word/document.xml": "<w:document/>"}).items():
            archive.writestr(name, text)
    return buffer.getvalue()


def send(client, content=PDF_BYTES, filename="Meu Currículo.pdf", consent="true", version="v1"):
    data = {"consent": consent, "consent_version": version}
    return client.post("/curriculos", files={"file": (filename, content)}, data=data)


def test_envia_pdf_com_consentimento(client, store):
    response = send(client)

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "Meu Currículo.pdf"
    assert body["content_type"] == PDF
    assert body["size_bytes"] == len(PDF_BYTES)

    assert store.consents == [{"user_id": USER_ID, "purpose": "analise_curriculo", "version": "v1"}]
    [(path, content)] = store.files.items()
    assert path.startswith(f"{USER_ID}/") and path.endswith(".pdf")
    assert "Currículo" not in path  # o nome no Storage é aleatório
    assert content == PDF_BYTES
    assert store.resumes[0]["storage_path"] == path
    assert store.resumes[0]["consent_id"] == "consent-1"


def test_envia_docx(client, store):
    response = send(client, content=docx_bytes(), filename="cv.docx")

    assert response.status_code == 201
    assert response.json()["content_type"] == DOCX
    assert next(iter(store.files)).endswith(".docx")


def test_recusa_sem_consentimento(client, store):
    response = send(client, consent="false")

    assert response.status_code == 400
    assert "aceite o termo" in response.json()["detail"]
    assert store.consents == []
    assert store.files == {}


def test_recusa_termo_desatualizado(client, store):
    response = send(client, version="v0")

    assert response.status_code == 409
    assert store.files == {}


def test_recusa_arquivo_maior_que_5_mb(client, store):
    response = send(client, content=b"%PDF-" + b"0" * MAX_BYTES)

    assert response.status_code == 413
    assert store.files == {}


@pytest.mark.parametrize(
    ("descricao", "content"),
    [
        ("executável renomeado para .pdf", b"MZ\x90\x00 programa"),
        ("zip que não é Word", docx_bytes({"planilha.xml": "<x/>"})),
        ("zip corrompido", b"PK\x03\x04 isto nao e um zip"),
        ("arquivo vazio", b""),
    ],
)
def test_recusa_arquivo_que_nao_e_pdf_nem_docx(client, store, descricao, content):
    response = send(client, content=content, filename="cv.pdf")

    assert response.status_code == 415, descricao
    assert response.json()["detail"] == "Envie o currículo em PDF ou DOCX."
    assert store.files == {}


def test_apaga_o_arquivo_se_nao_conseguir_registrar(client, store):
    store.fail_on.add("resume")

    response = send(client)

    assert response.status_code == 502
    assert store.files == {}  # nada órfão no Storage


def test_nao_registra_se_o_upload_falhar(client, store):
    store.fail_on.add("upload")

    response = send(client)

    assert response.status_code == 502
    assert store.resumes == []


def test_lista_os_curriculos_do_mais_recente_para_o_mais_antigo(client, store):
    send(client, filename="primeiro.pdf")
    send(client, filename="segundo.pdf")

    response = client.get("/curriculos")

    assert response.status_code == 200
    assert [r["original_filename"] for r in response.json()] == ["segundo.pdf", "primeiro.pdf"]


def test_lista_avisa_quando_o_supabase_falha(client, store):
    store.fail_on.add("list")

    assert client.get("/curriculos").status_code == 502


def test_exige_login():
    app = create_app()
    app.dependency_overrides[get_token_verifier] = lambda: None

    assert TestClient(app).post("/curriculos").status_code == 401
    assert TestClient(app).get("/curriculos").status_code == 401


@pytest.mark.parametrize(
    ("original", "esperado"),
    [
        ("Meu CV.pdf", "Meu CV.pdf"),
        ("C:\\Users\\ana\\Documentos\\cv.pdf", "cv.pdf"),
        ("../../etc/passwd", "passwd"),
        ("   ", "curriculo.pdf"),
        (None, "curriculo.pdf"),
        ("a" * 300 + ".pdf", "a" * 255),
    ],
)
def test_limpa_o_nome_original(original, esperado):
    assert clean_filename(original, PDF) == esperado


def test_detecta_tipo_pelo_conteudo():
    assert detect_content_type(PDF_BYTES) == PDF
    assert detect_content_type(docx_bytes()) == DOCX
    assert detect_content_type(b"texto qualquer") is None


@pytest.mark.anyio
async def test_store_indisponivel_sem_supabase_configurado():
    session = UserSession(user=CurrentUser(id=USER_ID), access_token="t")
    generator = get_resume_store(session, Settings(_env_file=None, supabase_url=""))

    with pytest.raises(HTTPException) as exc:
        await anext(generator)

    assert exc.value.status_code == 503


@pytest.mark.anyio
async def test_store_age_em_nome_do_usuario_logado():
    session = UserSession(user=CurrentUser(id=USER_ID), access_token="token-da-ana")
    settings = Settings(
        _env_file=None, supabase_url="https://exemplo.supabase.co", supabase_anon_key="publica"
    )
    generator = get_resume_store(session, settings)

    store = await anext(generator)

    assert isinstance(store, SupabaseUserClient)
    assert store._headers["Authorization"] == "Bearer token-da-ana"
    await generator.aclose()


def test_exclui_o_curriculo_e_o_arquivo(client, store):
    resume_id = send(client).json()["id"]

    response = client.delete(f"/curriculos/{resume_id}")

    assert response.status_code == 204
    assert store.resumes == []
    assert store.files == {}


def test_exclusao_de_curriculo_inexistente_ou_de_outra_pessoa_responde_404(client, store):
    # Pelo RLS, o currículo de outra pessoa simplesmente não aparece: mesmo efeito.
    response = client.delete("/curriculos/99999999-9999-9999-9999-999999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Currículo não encontrado."


def test_exclusao_recusa_id_que_nao_e_uuid(client):
    assert client.delete("/curriculos/abc").status_code == 422


def test_se_falhar_ao_apagar_o_registro_o_arquivo_ja_foi_apagado(client, store):
    resume_id = send(client).json()["id"]
    store.fail_on.add("delete_resume")

    response = client.delete(f"/curriculos/{resume_id}")

    assert response.status_code == 502
    assert store.files == {}  # nunca sobra arquivo esquecido; tentar de novo apaga o registro
