import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.config import Settings
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError
from tests.conftest import USER_ID


class FakeAdmin:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.fail = False

    async def delete_user(self, user_id: str) -> None:
        if self.fail:
            raise SupabaseError("admin")
        self.deleted.append(user_id)


@pytest.fixture
def admin(client) -> FakeAdmin:
    fake = FakeAdmin()
    client.app.dependency_overrides[get_supabase_admin] = lambda: fake
    return fake


def test_exclui_a_conta_e_todos_os_arquivos(client: TestClient, store, admin):
    store.files = {
        f"{USER_ID}/a.pdf": b"%PDF-",
        f"{USER_ID}/orfao.pdf": b"%PDF-",  # arquivo sem registro também vai embora
        "22222222-2222-2222-2222-222222222222/b.pdf": b"%PDF-",  # de outra pessoa: fica
    }

    response = client.delete("/conta")

    assert response.status_code == 204
    assert admin.deleted == [USER_ID]
    assert list(store.files) == ["22222222-2222-2222-2222-222222222222/b.pdf"]


def test_nao_apaga_a_conta_se_nao_conseguir_apagar_os_arquivos(client, store, admin):
    store.files = {f"{USER_ID}/a.pdf": b"%PDF-"}
    store.fail_on.add("delete_files")

    response = client.delete("/conta")

    assert response.status_code == 502
    assert admin.deleted == []  # a conta continua, e a pessoa pode tentar de novo


def test_falha_ao_apagar_a_conta_permite_tentar_de_novo(client, store, admin):
    store.files = {f"{USER_ID}/a.pdf": b"%PDF-"}
    admin.fail = True

    assert client.delete("/conta").status_code == 502

    admin.fail = False
    assert client.delete("/conta").status_code == 204
    assert admin.deleted == [USER_ID]


@pytest.mark.anyio
async def test_admin_indisponivel_sem_chave_secreta():
    generator = get_supabase_admin(
        Settings(_env_file=None, supabase_url="https://x.supabase.co", supabase_service_role_key="")
    )

    with pytest.raises(HTTPException) as exc:
        await anext(generator)

    assert exc.value.status_code == 503


@pytest.mark.anyio
async def test_admin_usa_a_chave_secreta():
    generator = get_supabase_admin(
        Settings(
            _env_file=None,
            supabase_url="https://x.supabase.co",
            supabase_service_role_key="secreta",
        )
    )

    admin = await anext(generator)

    assert isinstance(admin, SupabaseAdminClient)
    assert admin._headers["apikey"] == "secreta"
    await generator.aclose()
