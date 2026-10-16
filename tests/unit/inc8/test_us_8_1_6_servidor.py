"""El servidor sirve la API bajo `/api` y el frontend compilado en la raíz (US-8.1.6)."""

import tomllib
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import src.app
from src.servidor import crear_servidor

_RAIZ = Path(__file__).resolve().parents[3]
_INDEX = "<!doctype html><title>cognion-spa</title>"


@pytest.fixture(name="frontend")
def _frontend(tmp_path: Path) -> Path:
    """Un `dist` mínimo: `index.html` y un asset."""
    (tmp_path / "index.html").write_text(_INDEX, encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("ruta", ["/", "/materias/123", "/login"])
def test_rutas_del_spa_devuelven_index(frontend: Path, ruta: str) -> None:
    """Escenario 1: la raíz y las rutas del SPA responden `index.html`."""
    resp = TestClient(crear_servidor(frontend)).get(ruta)
    assert resp.status_code == 200
    assert "cognion-spa" in resp.text


def test_asset_existente_se_sirve_e_inexistente_es_404(frontend: Path) -> None:
    """Escenario 2: un build roto no se disfraza de `index.html`."""
    cliente = TestClient(crear_servidor(frontend))
    assert cliente.get("/assets/app.js").text == "console.log('ok')"
    assert cliente.get("/assets/falta.js").status_code == 404


def test_la_api_vive_bajo_api_y_no_la_pisa_el_spa(frontend: Path) -> None:
    """Escenario 3: `/api/materias` es la API (401 sin token), `/materias` es el SPA."""
    cliente = TestClient(crear_servidor(frontend))
    assert cliente.get("/api/health").json() == {"status": "ok"}
    api = cliente.get("/api/materias")
    assert api.status_code in (401, 403)
    assert "cognion-spa" not in api.text
    assert "cognion-spa" in cliente.get("/materias").text


def test_sin_frontend_solo_queda_la_api(tmp_path: Path) -> None:
    """Escenario 4: en desarrollo no hay `dist`; `/` es 404 y la API sigue."""
    cliente = TestClient(crear_servidor(tmp_path / "no-existe"))
    assert cliente.get("/").status_code == 404
    assert cliente.get("/api/health").status_code == 200


def test_el_lifespan_de_la_api_se_ejecuta(frontend: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Escenario 5: Starlette no corre el lifespan de una app montada; el servidor lo propaga."""
    arrancado: list[bool] = []

    async def _tarea_falsa() -> None:
        arrancado.append(True)

    monkeypatch.setattr(src.app, "_verificar_vencimientos_periodicamente", _tarea_falsa)
    with TestClient(crear_servidor(frontend)) as cliente:
        cliente.get("/api/health")
    assert arrancado == [True]


def test_websocket_bajo_api_llega_a_la_api(frontend: Path) -> None:
    """Escenario 6: el canal en vivo bajo `/api` lo atiende la API (rechaza el token inválido)."""
    cliente = TestClient(crear_servidor(frontend))
    with pytest.raises(WebSocketDisconnect) as info:
        with cliente.websocket_connect(f"/api/sesiones-en-vivo/{uuid4()}/canal?token=invalido"):
            pass
    assert info.value.code == 1008


def test_dockerfile_arranca_el_servidor_y_embebe_la_base_api() -> None:
    """El `CMD` usa `src.servidor:servidor` con proxy headers y el build usa `/api`."""
    dockerfile = (_RAIZ / "Dockerfile").read_text(encoding="utf-8")
    cmd = next(linea for linea in dockerfile.splitlines() if linea.startswith("CMD"))
    assert "src.servidor:servidor" in cmd
    assert "--proxy-headers" in cmd
    assert 'ARG VITE_API_BASE_URL="/api"' in dockerfile


def test_fly_toml_chequea_la_salud_bajo_api() -> None:
    """Con la API montada en `/api`, el healthcheck de Fly debe apuntar ahí."""
    config = tomllib.loads((_RAIZ / "fly.toml").read_text(encoding="utf-8"))
    assert config["http_service"]["checks"][0]["path"] == "/api/health"
