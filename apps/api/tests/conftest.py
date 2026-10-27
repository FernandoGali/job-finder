"""Peças compartilhadas pelos testes da API."""

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jobfinder_api.auth import CurrentUser, UserSession, get_session
from jobfinder_api.main import create_app
from jobfinder_api.resumes import get_resume_store
from jobfinder_api.supabase_user import SupabaseError

USER_ID = "11111111-1111-1111-1111-111111111111"


class FakeStore:
    """Supabase de mentira, em memória, que pode ser configurado para falhar."""

    def __init__(self) -> None:
        self.consents: list[dict[str, str]] = []
        self.files: dict[str, bytes] = {}
        self.resumes: list[dict[str, Any]] = []
        self.fail_on: set[str] = set()

    def _maybe_fail(self, step: str) -> None:
        if step in self.fail_on:
            raise SupabaseError(step)

    async def add_consent(self, user_id: str, purpose: str, version: str) -> str:
        self._maybe_fail("consent")
        self.consents.append({"user_id": user_id, "purpose": purpose, "version": version})
        return f"consent-{len(self.consents)}"

    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        self._maybe_fail("upload")
        self.files[path] = content

    async def delete_upload(self, path: str) -> None:
        self.files.pop(path)

    async def add_resume(self, resume: dict[str, Any]) -> dict[str, Any]:
        self._maybe_fail("resume")
        row = {**resume, "id": str(uuid.uuid4()), "uploaded_at": "2026-10-27T18:00:00Z"}
        self.resumes.append(row)
        return row

    async def list_resumes(self) -> list[dict[str, Any]]:
        self._maybe_fail("list")
        return list(reversed(self.resumes))

    async def get_resume_file(self, resume_id: str) -> dict[str, str] | None:
        self._maybe_fail("get_file")
        row = next((r for r in self.resumes if r["id"] == resume_id), None)
        return {k: row[k] for k in ("storage_path", "content_type")} if row else None

    async def download(self, path: str) -> bytes:
        return self.files[path]

    async def get_resume_path(self, resume_id: str) -> str | None:
        return next((r["storage_path"] for r in self.resumes if r["id"] == resume_id), None)

    async def delete_resume(self, resume_id: str) -> None:
        self._maybe_fail("delete_resume")
        self.resumes = [r for r in self.resumes if r["id"] != resume_id]

    async def list_files(self, user_id: str) -> list[str]:
        return [path for path in self.files if path.startswith(f"{user_id}/")]

    async def delete_files(self, paths: list[str]) -> None:
        self._maybe_fail("delete_files")
        for path in paths:
            self.files.pop(path, None)


@pytest.fixture
def store() -> FakeStore:
    return FakeStore()


@pytest.fixture
def client(store) -> TestClient:
    """API com a Ana logada e o Supabase de mentira no lugar do real."""
    app = create_app()
    app.dependency_overrides[get_session] = lambda: UserSession(
        user=CurrentUser(id=USER_ID, email="ana@exemplo.com"), access_token="token-da-ana"
    )
    app.dependency_overrides[get_resume_store] = lambda: store
    return TestClient(app)


def pdf_with_text(*lines: str) -> bytes:
    """Monta um PDF mínimo de verdade, com texto selecionável (só caracteres ASCII)."""
    commands = " ".join(f"({line}) Tj 0 -14 Td" for line in lines)
    stream = f"BT /F1 12 Tf 72 720 Td {commands} ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n".encode()
    return out + b"%%EOF\n"  # o marcador de fim do PDF tem mesmo dois %
