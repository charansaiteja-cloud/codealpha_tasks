import pytest
from fastapi.testclient import TestClient

import app.main as main

client = TestClient(main.app)


def test_health_and_headers():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "0"
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert response.headers.get("Permissions-Policy")
    assert "default-src 'none'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("Strict-Transport-Security")


def test_auth_required(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get("/api/v1/demo")
    assert response.status_code == 401


def test_wrong_key_rejected(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get("/api/v1/demo", headers={"X-API-Key": "wrongkey"})
    assert response.status_code == 401


def test_missing_config_fails_closed(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "")
    response = client.get("/api/v1/demo", headers={"X-API-Key": "anykey"})
    assert response.status_code == 401


def test_whitespace_only_config_fails_closed(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "   ")
    response = client.get("/api/v1/demo", headers={"X-API-Key": "   "})
    assert response.status_code == 401


def test_oversized_api_key_rejected(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get(
        "/api/v1/demo",
        headers={"X-API-Key": "x" * 4097},
    )
    assert response.status_code == 401


def test_read_demo(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get("/api/v1/demo", headers={"X-API-Key": "secret123"})
    assert response.status_code == 200
    assert "tables" in response.json()
    assert "items" in response.json()["tables"]


def test_invalid_id(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get("/items/0", headers={"X-API-Key": "secret123"})
    assert response.status_code == 400


def test_oversized_sqlite_id_is_rejected(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get(
        f"/items/{main.SQLITE_MAX_INTEGER + 1}",
        headers={"X-API-Key": "secret123"},
    )
    assert response.status_code == 400


def test_largest_sqlite_id_is_bound_safely(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get(
        f"/items/{main.SQLITE_MAX_INTEGER}",
        headers={"X-API-Key": "secret123"},
    )
    assert response.status_code == 404


def test_not_found(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.get("/items/99999", headers={"X-API-Key": "secret123"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "name",
    ["", "x" * 65, "   ", "control\x00character", "line\nbreak"],
)
def test_invalid_names(monkeypatch, name):
    monkeypatch.setattr(main, "API_KEY", "secret123")
    response = client.post(
        "/items",
        json={"name": name},
        headers={"X-API-Key": "secret123"},
    )
    assert response.status_code in (400, 422)


def test_create_and_search(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(main, "API_KEY", "secret123")

    res = client.post(
        "/items",
        json={"name": "AlphaSecurityItem"},
        headers={"X-API-Key": "secret123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "AlphaSecurityItem"
    assert "id" in data

    res2 = client.get(
        "/items?q=AlphaSecurity",
        headers={"X-API-Key": "secret123"},
    )
    assert res2.status_code == 200
    items = res2.json().get("items", [])
    assert any(item["name"] == "AlphaSecurityItem" for item in items)


def test_search_boundaries(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(main, "API_KEY", "secret123")

    res = client.get(
        "/items?q=nonexistentitemxyz123",
        headers={"X-API-Key": "secret123"},
    )
    assert res.status_code == 200
    assert res.json().get("items") == []


def test_sql_metacharacters_are_data(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(main, "API_KEY", "secret123")

    malicious_input = "' OR '1'='1"
    res = client.post(
        "/items",
        json={"name": malicious_input},
        headers={"X-API-Key": "secret123"},
    )
    assert res.status_code == 201

    res2 = client.get(
        "/items",
        params={"q": malicious_input},
        headers={"X-API-Key": "secret123"},
    )
    assert res2.status_code == 200
    items = res2.json().get("items", [])
    assert len(items) == 1
    assert items[0]["name"] == malicious_input


def test_like_wildcards_are_treated_as_literal_text(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(main, "API_KEY", "secret123")
    headers = {"X-API-Key": "secret123"}

    for name in ("Percent%Item", "Underscore_Item", "PlainItem"):
        response = client.post("/items", json={"name": name}, headers=headers)
        assert response.status_code == 201

    percent_results = client.get(
        "/items", params={"q": "%"}, headers=headers
    ).json()["items"]
    assert [item["name"] for item in percent_results] == ["Percent%Item"]

    underscore_results = client.get(
        "/items", params={"q": "_"}, headers=headers
    ).json()["items"]
    assert [item["name"] for item in underscore_results] == ["Underscore_Item"]


def test_database_creates_missing_nested_directory(monkeypatch, tmp_path):
    nested_db = tmp_path / "deep" / "nested" / "path" / "test.sqlite3"
    monkeypatch.setattr(main, "DB_PATH", nested_db)
    monkeypatch.setattr(main, "API_KEY", "secret123")

    res = client.post(
        "/items",
        json={"name": "NestedDirTest"},
        headers={"X-API-Key": "secret123"},
    )
    assert res.status_code == 201
    assert nested_db.exists()
