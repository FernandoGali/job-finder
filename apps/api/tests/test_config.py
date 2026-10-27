from jobfinder_api import config


def test_env_file_fica_na_raiz_do_projeto():
    # O .env fica na raiz do monorepo, ao lado do .env.example, e não em apps/api.
    assert (config.ROOT_ENV_FILE.parent / ".env.example").is_file()


def test_get_settings_le_o_env_da_raiz_mesmo_rodando_de_outra_pasta(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("SUPABASE_URL=https://exemplo.supabase.co\nSUPABASE_ANON_KEY=chave\n")
    monkeypatch.setattr(config, "ROOT_ENV_FILE", env)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.chdir(tmp_path.parent)
    config.get_settings.cache_clear()

    try:
        assert config.get_settings().supabase_configured is True
    finally:
        config.get_settings.cache_clear()
