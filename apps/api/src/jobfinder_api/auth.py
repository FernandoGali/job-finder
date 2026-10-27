"""Reconhece quem está logado a partir do token (JWT) que o Supabase dá ao usuário.

O Supabase assina o token com uma chave privada; a API confere a assinatura com a
chave pública que ele publica (JWKS). Nenhuma chave secreta é necessária aqui.
"""

from collections.abc import Callable
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from jobfinder_api.config import Settings, get_settings

# Só algoritmos assimétricos: impede que alguém assine um token com a chave pública.
ALGORITHMS = ["ES256", "RS256"]
AUDIENCE = "authenticated"


class CurrentUser(BaseModel):
    id: str
    email: str | None = None


class InvalidTokenError(Exception):
    pass


class AuthUnavailableError(Exception):
    pass


class TokenVerifier:
    def __init__(self, signing_key_for: Callable[[str], Any], issuer: str) -> None:
        self._signing_key_for = signing_key_for
        self._issuer = issuer

    def verify(self, token: str) -> CurrentUser:
        try:
            key = self._signing_key_for(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                audience=AUDIENCE,
                issuer=self._issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
        except jwt.PyJWKClientConnectionError as exc:
            raise AuthUnavailableError from exc
        except jwt.PyJWTError as exc:
            raise InvalidTokenError from exc
        return CurrentUser(id=claims["sub"], email=claims.get("email"))


@lru_cache
def _verifier_for(supabase_url: str) -> TokenVerifier:
    jwks = jwt.PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json", cache_keys=True)
    return TokenVerifier(
        signing_key_for=lambda token: jwks.get_signing_key_from_jwt(token).key,
        issuer=f"{supabase_url}/auth/v1",
    )


def get_token_verifier(settings: Settings = Depends(get_settings)) -> TokenVerifier:
    if not settings.supabase_url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Login indisponível no momento.")
    return _verifier_for(settings.supabase_url.rstrip("/"))


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> CurrentUser:
    """Dependência das rotas que exigem login. Responde 401 se o token faltar ou for inválido."""
    if credentials is None:
        raise _unauthorized("Faça login para continuar.")
    try:
        return verifier.verify(credentials.credentials)
    except InvalidTokenError:
        raise _unauthorized("Sessão inválida ou expirada. Entre de novo.") from None
    except AuthUnavailableError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Login indisponível no momento."
        ) from None


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )
