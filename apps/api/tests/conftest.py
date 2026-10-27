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
