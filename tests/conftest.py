from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from foundry_showcase.main import create_app
from foundry_showcase.settings import DEFAULT_CATALOG_PATH, Settings


@pytest.fixture
def client() -> Iterator[TestClient]:
    application = create_app(Settings(catalog_path=DEFAULT_CATALOG_PATH))
    with TestClient(application, follow_redirects=False) as test_client:
        yield test_client
