"""Tests for the HTTP endpoints that wire the engine to the frontend."""
from fastapi.testclient import TestClient

from app.main import API_VERSION, app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["version"] == API_VERSION


def test_sightings_still_works():
    r = client.get("/api/sightings")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


class TestScoreEndpoint:
    def test_returns_full_payload(self):
        r = client.post("/api/score", json={"lat": 42.33, "lon": -71.1})
        assert r.status_code == 200
        body = r.json()
        for key in ("site_score", "e_final", "grade", "subscores",
                    "categories", "species", "data_confidence", "location"):
            assert key in body, f"missing {key}"
        assert set(body["subscores"]) == {"S_H", "S_K", "S_C", "S_Cb", "S_L", "S_G"}
        assert 0 <= body["site_score"] <= 100

    def test_echoes_clicked_location(self):
        r = client.post("/api/score", json={"lat": 42.5, "lon": -71.9})
        assert r.json()["location"] == {"lat": 42.5, "lon": -71.9}

    def test_rejects_bad_coords(self):
        assert client.post("/api/score", json={"lat": 999, "lon": 0}).status_code == 422
        assert client.post("/api/score", json={"lat": 0, "lon": 999}).status_code == 422


class TestReportEndpoint:
    def test_returns_markdown(self):
        r = client.post("/api/report", json={"lat": 42.33, "lon": -71.1})
        assert r.status_code == 200
        body = r.json()
        assert "markdown" in body
        md = body["markdown"]
        assert md.startswith("# Environmental Impact Report")
        # Key sections present.
        for heading in ("Habitat Integrity", "Keystone Species Impact",
                        "Data-Confidence Adjustment", "Methodology & Limitations"):
            assert heading in md

    def test_report_reflects_clicked_location(self):
        r = client.post("/api/report", json={"lat": 42.25, "lon": -71.33})
        md = r.json()["markdown"]
        assert "42.25" in md or "42.2500" in md


class TestCORS:
    def test_cors_allows_frontend_origin(self):
        r = client.options(
            "/api/score",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Preflight should be allowed for the configured frontend origin.
        assert r.status_code in (200, 204)
        assert r.headers.get("access-control-allow-origin") == "http://localhost:8000"
