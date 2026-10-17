"""Preflight CORS contra la app real con orígenes configurados (US-8.1.1)."""

from fastapi.testclient import TestClient

from src.app import app

_PERMITIDO = "http://localhost:5173"


def _preflight(origin: str):
    return TestClient(app).options(
        "/identidad/login",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_origen_permitido_recibe_header() -> None:
    """El origen configurado recibe `Access-Control-Allow-Origin`."""
    resp = _preflight(_PERMITIDO)
    assert resp.headers["access-control-allow-origin"] == _PERMITIDO


def test_origen_no_listado_no_recibe_header() -> None:
    """Un origen no listado no recibe el header CORS."""
    resp = _preflight("https://intruso.example")
    assert "access-control-allow-origin" not in resp.headers
