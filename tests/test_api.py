from unittest.mock import patch

from fastapi.testclient import TestClient

from foundry_showcase.main import create_app
from foundry_showcase.settings import DEFAULT_CATALOG_PATH, Settings


def test_health_is_anonymous_and_does_not_redirect(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "location" not in response.headers


def test_ready_checks_only_the_local_catalog(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "scope": "local_catalog_only",
        "live_demos_enabled": False,
    }


def test_catalog_is_synthetic_and_not_executable(client: TestClient) -> None:
    response = client.get("/api/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_classification"] == "synthetic"
    assert payload["source_verification"] == "pending"
    assert payload["live_demos_enabled"] is False
    assert len({item["category"] for item in payload["capabilities"]}) == 9
    for capability in payload["capabilities"]:
        assert capability["deployment_status"] == "not_deployed"
        assert capability["execution_enabled"] is False
        assert capability["source_verification"] == "pending"


def test_status_distinguishes_targets_from_implemented_controls(client: TestClient) -> None:
    response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stage"] == "local_foundation"
    assert payload["readiness_scope"] == "local_catalog_only"
    assert payload["deployment_status"] == "not_deployed"
    for field in (
        "live_demos_enabled",
        "authentication_implemented",
        "visitor_approval_implemented",
        "session_accounting_implemented",
        "cloud_security_state_implemented",
        "live_sdk_execution_implemented",
    ):
        assert payload[field] is False
    assert payload["planned_constraints"] == {
        "enforcement": "not_implemented",
        "visitor_access": "approved_visitors_email_otp",
        "session_minutes": 15,
        "sessions_per_visitor_per_day": 3,
        "monthly_budget_target_usd": 100,
    }


def test_missing_catalog_keeps_liveness_but_fails_readiness() -> None:
    settings = Settings(
        catalog_path=DEFAULT_CATALOG_PATH.with_name("catalog-intentionally-missing.json")
    )
    with TestClient(create_app(settings), follow_redirects=False) as unhealthy_client:
        assert unhealthy_client.get("/healthz").status_code == 200
        readiness = unhealthy_client.get("/readyz")
        assert readiness.status_code == 503
        assert readiness.json()["status"] == "not_ready"
        assert readiness.json()["scope"] == "local_catalog_only"
        response = unhealthy_client.get("/api/catalog")
        assert response.status_code == 503
        assert "capabilities" not in response.json()


def test_malformed_catalog_never_falls_back_to_success(client: TestClient) -> None:
    with patch("foundry_showcase.registry.Path.read_bytes", return_value=b"{broken"):
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503
        assert client.get("/api/catalog").status_code == 503


def test_approved_origin_can_read_metadata_without_credentials(client: TestClient) -> None:
    response = client.options(
        "/api/catalog",
        headers={
            "Origin": "https://chadhage.github.io",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://chadhage.github.io"
    assert "access-control-allow-credentials" not in response.headers


def test_other_origins_and_execution_methods_are_not_allowed(client: TestClient) -> None:
    for origin in (
        "https://unapproved.invalid",
        "https://chadhage.github.io/azure-ai-foundry-irl",
        "http://localhost:8080",
    ):
        response = client.options(
            "/api/catalog",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers

    response = client.options(
        "/api/catalog",
        headers={
            "Origin": "https://chadhage.github.io",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert client.post("/api/catalog", json={}).status_code == 405
    assert client.post("/api/demo", json={}).status_code == 404
    assert client.post("/api/sessions", json={}).status_code == 404
