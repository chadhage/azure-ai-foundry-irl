"""Explicit local configuration; no cloud discovery or credential handling."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = REPOSITORY_ROOT / "data" / "catalog.json"
DEFAULT_ALLOWED_ORIGINS = ("https://chadhage.github.io",)


def validate_origin(origin: str) -> None:
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("CORS origins must be valid HTTP(S) origins.") from exc

    if (
        not origin
        or origin != origin.strip()
        or "*" in origin
        or parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "CORS origins must be explicit HTTP(S) origins without paths, "
            "credentials, wildcards, queries, or fragments."
        )


@dataclass(frozen=True)
class Settings:
    catalog_path: Path = DEFAULT_CATALOG_PATH
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS

    def __post_init__(self) -> None:
        if not self.allowed_origins:
            raise ValueError("At least one explicit CORS origin is required.")
        for origin in self.allowed_origins:
            validate_origin(origin)

    @classmethod
    def from_environment(cls) -> "Settings":
        raw_path = os.environ.get("CATALOG_PATH")
        catalog_path = Path(raw_path) if raw_path else DEFAULT_CATALOG_PATH
        if not catalog_path.is_absolute():
            catalog_path = REPOSITORY_ROOT / catalog_path

        raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS")
        allowed_origins = (
            tuple(origin.strip() for origin in raw_origins.split(","))
            if raw_origins is not None
            else DEFAULT_ALLOWED_ORIGINS
        )
        return cls(catalog_path=catalog_path, allowed_origins=allowed_origins)
