from pathlib import Path

import pytest

from foundry_showcase.settings import (
    DEFAULT_ALLOWED_ORIGINS,
    DEFAULT_CATALOG_PATH,
    REPOSITORY_ROOT,
    Settings,
)


def test_defaults_do_not_require_cloud_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CATALOG_PATH", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    settings = Settings.from_environment()
    assert settings.catalog_path == DEFAULT_CATALOG_PATH
    assert settings.allowed_origins == DEFAULT_ALLOWED_ORIGINS


def test_relative_registry_and_explicit_local_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CATALOG_PATH", str(Path("data") / "catalog.json"))
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://chadhage.github.io, http://127.0.0.1:8080",
    )
    settings = Settings.from_environment()
    assert settings.catalog_path == REPOSITORY_ROOT / "data" / "catalog.json"
    assert settings.allowed_origins == (
        "https://chadhage.github.io",
        "http://127.0.0.1:8080",
    )


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "*",
        "https://*.example.invalid",
        "https://chadhage.github.io/",
        "https://chadhage.github.io/azure-ai-foundry-irl",
        "https://visitor:secret@example.invalid",
        "https://example.invalid?mode=all",
        "https://example.invalid#catalog",
        "file://local",
        "https://example.invalid:not-a-port",
    ],
)
def test_unsafe_or_non_origin_cors_configuration_fails(origin: str) -> None:
    with pytest.raises(ValueError):
        Settings(allowed_origins=(origin,))


def test_empty_origin_list_fails() -> None:
    with pytest.raises(ValueError):
        Settings(allowed_origins=())
