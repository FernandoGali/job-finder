"""Envio e listagem do currículo. Exige login e consentimento (LGPD)."""

import io
import logging
import uuid
import zipfile
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import PurePath
from typing import Any, Protocol

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from jobfinder_api.auth import UserSession, get_session
from jobfinder_api.config import Settings, get_settings
from jobfinder_api.resume_analysis import SuggestedRole
from jobfinder_api.supabase_user import SupabaseError, SupabaseUserClient

logger = logging.getLogger(__name__)

MAX_BYTES = 5 * 1024 * 1024
CONSENT_PURPOSE = "analise_curriculo"
# Versão do termo mostrado na tela. Mudou o texto do termo? Suba a versão aqui e na tela.
CONSENT_VERSION = "v1"

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
EXTENSIONS = {PDF: "pdf", DOCX: "docx"}


class ProfileOut(BaseModel):
    target_role: str | None
    seniority: str | None
    skills: list[str]
    certifications: list[str] = []
    suggested_roles: list[SuggestedRole] = []
    search_terms: list[str] = []
    summary: str
    analyzed_at: datetime


class ResumeOut(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    profile: ProfileOut | None = None


class ResumeStore(Protocol):
    async def add_consent(self, user_id: str, purpose: str, version: str) -> str: ...
    async def upload(self, path: str, content: bytes, content_type: str) -> None: ...
    async def delete_upload(self, path: str) -> None: ...
    async def add_resume(self, resume: dict[str, Any]) -> dict[str, Any]: ...
    async def list_resumes(self) -> list[dict[str, Any]]: ...
    async def get_resume_path(self, resume_id: str) -> str | None: ...
    async def get_resume_file(self, resume_id: str) -> dict[str, str] | None: ...
    async def download(self, path: str) -> bytes: ...
    async def delete_resume(self, resume_id: str) -> None: ...
    async def list_files(self, user_id: str) -> list[str]: ...
    async def delete_files(self, paths: list[str]) -> None: ...


async def get_resume_store(
    session: UserSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[ResumeStore]:
    if not settings.supabase_configured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Envio indisponível no momento.")
    async with httpx.AsyncClient(timeout=30) as http:
        yield SupabaseUserClient(
            settings.supabase_url, settings.supabase_anon_key, session.access_token, http
        )


def detect_content_type(content: bytes) -> str | None:
    """Descobre o tipo pelo conteúdo, não pelo nome: um .exe renomeado para .pdf é recusado."""
    if content.startswith(b"%PDF-"):
        return PDF
    if content.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if "word/document.xml" in archive.namelist():
                    return DOCX
        except zipfile.BadZipFile:
            return None
    return None


def clean_filename(filename: str | None, content_type: str) -> str:
    """Nome original só para exibir: sem pastas, com tamanho limitado."""
    name = PurePath((filename or "").replace("\\", "/")).name.strip()
    return name[:255] or f"curriculo.{EXTENSIONS[content_type]}"


router = APIRouter()


@router.post("/curriculos", status_code=status.HTTP_201_CREATED, response_model=ResumeOut)
async def upload_resume(
    file: UploadFile,
    consent: bool = Form(False),
    consent_version: str = Form(""),
    session: UserSession = Depends(get_session),
    store: ResumeStore = Depends(get_resume_store),
) -> ResumeOut:
    if not consent:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Para enviar o currículo, aceite o termo de uso dos dados."
        )
    if consent_version != CONSENT_VERSION:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "O termo foi atualizado. Recarregue a página e aceite de novo.",
        )

    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "O arquivo passa de 5 MB.")
    content_type = detect_content_type(content)
    if content_type is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Envie o currículo em PDF ou DOCX."
        )

    user_id = session.user.id
    path = f"{user_id}/{uuid.uuid4().hex}.{EXTENSIONS[content_type]}"
    try:
        consent_id = await store.add_consent(user_id, CONSENT_PURPOSE, CONSENT_VERSION)
        await store.upload(path, content, content_type)
        try:
            row = await store.add_resume(
                {
                    "user_id": user_id,
                    "consent_id": consent_id,
                    "storage_path": path,
                    "original_filename": clean_filename(file.filename, content_type),
                    "content_type": content_type,
                    "size_bytes": len(content),
                }
            )
        except SupabaseError:
            # Sem registro, o arquivo ficaria órfão no Storage: apaga antes de desistir.
            await store.delete_upload(path)
            raise
    except SupabaseError:
        logger.exception("Falha ao salvar currículo")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível salvar o currículo agora. Tente de novo."
        ) from None
    return ResumeOut(**row)


@router.get("/curriculos", response_model=list[ResumeOut])
async def list_resumes(store: ResumeStore = Depends(get_resume_store)) -> list[ResumeOut]:
    """Currículos da pessoa logada, do mais recente para o mais antigo."""
    try:
        rows = await store.list_resumes()
    except SupabaseError:
        logger.exception("Falha ao listar currículos")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível carregar seus currículos agora."
        ) from None
    return [ResumeOut(**row) for row in rows]


@router.delete("/curriculos/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID, store: ResumeStore = Depends(get_resume_store)
) -> None:
    """Apaga o arquivo e depois o registro: se algo falhar no meio, não sobra arquivo esquecido."""
    try:
        path = await store.get_resume_path(str(resume_id))
        if path is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Currículo não encontrado.")
        await store.delete_files([path])
        await store.delete_resume(str(resume_id))
    except SupabaseError:
        logger.exception("Falha ao excluir currículo")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Não foi possível excluir o currículo agora. Tente de novo.",
        ) from None
