import base64
import hmac
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.testclient import TestClient

from jobfinder_api.auth import TokenVerifier, get_token_verifier
from jobfinder_api.config import Settings
from jobfinder_api.main import create_app

ISSUER = "https://exemplo.supabase.co/auth/v1"
USER_ID = "8f0e6c3a-1b2c-4d5e-8f90-123456789abc"

# Par de chaves criado só para os testes, no lugar das chaves do Supabase.
PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


def make_token(key=PRIVATE_KEY, algorithm="ES256", **overrides) -> str:
    claims = {
        "sub": USER_ID,
        "email": "ana@exemplo.com",
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 3600,
        **overrides,
    }
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, key, algorithm=algorithm)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_token_verifier] = lambda: TokenVerifier(
        signing_key_for=lambda token: PRIVATE_KEY.public_key(), issuer=ISSUER
    )
    return TestClient(app)


def get_me(client: TestClient, token: str | None = None, scheme: str = "Bearer"):
    headers = {"Authorization": f"{scheme} {token}"} if token else {}
    return client.get("/me", headers=headers)


def test_me_reconhece_o_usuario_com_token_valido(client):
    response = get_me(client, make_token())

    assert response.status_code == 200
    assert response.json() == {"id": USER_ID, "email": "ana@exemplo.com"}


def test_me_exige_login(client):
    response = get_me(client)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["detail"] == "Faça login para continuar."


def test_me_recusa_quem_nao_usa_bearer(client):
    assert get_me(client, make_token(), scheme="Basic").status_code == 401


@pytest.mark.parametrize(
    ("descricao", "token"),
    [
        ("vencido", make_token(exp=int(time.time()) - 60)),
        ("assinado por outra chave", make_token(key=OTHER_PRIVATE_KEY)),
        ("feito para outro público", make_token(aud="anon")),
        ("emitido por outro projeto", make_token(iss="https://outro.supabase.co/auth/v1")),
        ("sem usuário", make_token(sub=None)),
        ("sem validade", make_token(exp=None)),
        ("sem assinatura (alg none)", make_token(key=None, algorithm="none")),
        ("lixo", "isto-nao-e-um-token"),
    ],
)
def test_me_recusa_token_invalido(client, descricao, token):
    response = get_me(client, token)

    assert response.status_code == 401, descricao
    assert response.json()["detail"] == "Sessão inválida ou expirada. Entre de novo."


def test_me_recusa_token_assinado_com_a_chave_publica_como_segredo(client):
    # Ataque clássico: usar a chave pública (que é conhecida) como senha do HS256.
    public_pem = PRIVATE_KEY.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Montado na mão: o próprio PyJWT se recusa a gerar esse token falso.
    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url(
        json.dumps(
            {"sub": "intruso", "aud": "authenticated", "iss": ISSUER, "exp": 9999999999}
        ).encode()
    )
    signature = b64url(hmac.new(public_pem, f"{header}.{payload}".encode(), "sha256").digest())

    assert get_me(client, f"{header}.{payload}.{signature}").status_code == 401


def test_me_responde_503_quando_nao_consegue_buscar_as_chaves_do_supabase():
    def offline(token):
        raise jwt.PyJWKClientConnectionError("sem rede")

    app = create_app()
    app.dependency_overrides[get_token_verifier] = lambda: TokenVerifier(offline, ISSUER)

    response = get_me(TestClient(app), make_token())

    assert response.status_code == 503


def test_verificador_usa_as_chaves_publicas_do_projeto_configurado():
    verifier = get_token_verifier(Settings(_env_file=None, supabase_url="https://abc.supabase.co/"))

    assert verifier._issuer == "https://abc.supabase.co/auth/v1"


def test_verificador_indisponivel_sem_supabase_configurado():
    with pytest.raises(HTTPException) as exc:
        get_token_verifier(Settings(_env_file=None, supabase_url=""))

    assert exc.value.status_code == 503
