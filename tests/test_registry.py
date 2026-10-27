import json
import logging
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from foundry_showcase.models import Catalog
from foundry_showcase.registry import MAX_CATALOG_BYTES, CatalogRegistry, CatalogUnavailable
from foundry_showcase.settings import DEFAULT_CATALOG_PATH


def test_registry_loads_the_file_backed_catalog() -> None:
    catalog = CatalogRegistry(DEFAULT_CATALOG_PATH).load()
    assert catalog.schema_version == 1
    assert catalog.capabilities


@pytest.mark.parametrize(
    "raw_catalog",
    [
        b"not-json",
        b"{}",
        b'{"schema_version": 1, "capabilities": []}',
        b"\xff",
    ],
)
def test_invalid_registry_is_logged_and_rejected(
    raw_catalog: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch("foundry_showcase.registry.Path.read_bytes", return_value=raw_catalog):
        with caplog.at_level(logging.ERROR), pytest.raises(CatalogUnavailable):
            CatalogRegistry(DEFAULT_CATALOG_PATH).load()
    assert "Local catalog dependency failed" in caplog.text
    assert raw_catalog.decode("utf-8", errors="replace") not in caplog.text


def test_oversized_registry_is_rejected() -> None:
    with patch(
        "foundry_showcase.registry.Path.read_bytes",
        return_value=b" " * (MAX_CATALOG_BYTES + 1),
    ):
        with pytest.raises(CatalogUnavailable):
            CatalogRegistry(DEFAULT_CATALOG_PATH).load()


@pytest.mark.parametrize(
    "change",
    ["empty", "duplicate-id", "enabled-execution", "enabled-demos", "non-synthetic", "unknown-field"],
)
def test_catalog_contract_rejects_misleading_or_invalid_metadata(change: str) -> None:
    payload = json.loads(DEFAULT_CATALOG_PATH.read_text(encoding="utf-8"))
    if change == "empty":
        payload["capabilities"] = []
    elif change == "duplicate-id":
        payload["capabilities"].append(payload["capabilities"][0])
    elif change == "enabled-execution":
        payload["capabilities"][0]["execution_enabled"] = True
    elif change == "enabled-demos":
        payload["live_demos_enabled"] = True
    elif change == "non-synthetic":
        payload["data_classification"] = "customer"
    else:
        payload["capabilities"][0]["endpoint"] = "/api/run"

    with pytest.raises(ValidationError):
        Catalog.model_validate_json(json.dumps(payload))
