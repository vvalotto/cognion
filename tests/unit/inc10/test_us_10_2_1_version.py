"""Versión única del proyecto (US-10.2.1): VERSION, pyproject, package.json, FastAPI, imagen y CD."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from src.app import app
from src.shared.frameworks.version import obtener_version

RAIZ = Path(__file__).resolve().parents[3]


def _version_archivo() -> str:
    return (RAIZ / "VERSION").read_text(encoding="utf-8").strip()


class TestVersionCoherente:
    """Escenarios 1 y 2: las cuatro versiones dicen lo mismo y la guarda indica cuál difiere."""

    def test_todas_las_versiones_coinciden_con_version(self) -> None:
        esperada = _version_archivo()
        pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
        paquete = json.loads((RAIZ / "frontend" / "package.json").read_text(encoding="utf-8"))
        bloqueo = json.loads((RAIZ / "frontend" / "package-lock.json").read_text(encoding="utf-8"))

        encontradas = {
            "pyproject.toml": pyproject["project"]["version"],
            "frontend/package.json": paquete["version"],
            "frontend/package-lock.json": bloqueo["version"],
            "frontend/package-lock.json (raíz del árbol)": bloqueo["packages"][""]["version"],
            "FastAPI": app.version,
        }
        distintas = {lugar: v for lugar, v in encontradas.items() if v != esperada}

        assert not distintas, f"Difieren de VERSION ({esperada}): {distintas}"

    def test_version_tiene_forma_de_semver(self) -> None:
        partes = _version_archivo().split(".")

        assert len(partes) == 3 and all(p.isdigit() for p in partes)


class TestObtenerVersion:
    """La lectura del archivo."""

    def test_devuelve_la_version_sin_espacios(self, tmp_path: Path) -> None:
        archivo = tmp_path / "VERSION"
        archivo.write_text("  2.3.4 \n", encoding="utf-8")

        assert obtener_version(archivo) == "2.3.4"

    def test_falla_si_el_archivo_no_existe(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="No se encontró"):
            obtener_version(tmp_path / "VERSION")

    def test_falla_si_el_archivo_esta_vacio(self, tmp_path: Path) -> None:
        archivo = tmp_path / "VERSION"
        archivo.write_text("\n", encoding="utf-8")

        with pytest.raises(RuntimeError, match="vacío"):
            obtener_version(archivo)


class TestHealthInformaLaVersion:
    """Escenarios 3 y 4."""

    def test_health_responde_estado_y_version(self) -> None:
        respuesta = TestClient(app).get("/health")

        assert respuesta.status_code == 200
        assert respuesta.json() == {"status": "ok", "version": _version_archivo()}


class TestImagenYCd:
    """Escenarios 5 y 7."""

    def test_el_dockerfile_copia_el_archivo_version(self) -> None:
        dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")

        assert "COPY VERSION" in dockerfile

    def test_el_archivo_version_no_lo_excluye_dockerignore(self) -> None:
        excluidos = (RAIZ / ".dockerignore").read_text(encoding="utf-8").splitlines()

        assert "VERSION" not in excluidos

    def test_el_cd_verifica_que_el_tag_coincida_con_version_antes_de_publicar(self) -> None:
        flujo = yaml.safe_load(
            (RAIZ / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
        )
        pasos = flujo["jobs"]["build-and-deploy"]["steps"]
        nombres = [paso.get("name", "") for paso in pasos]

        indice_verificacion = next(i for i, n in enumerate(nombres) if "coincide con VERSION" in n)
        indice_publicacion = next(
            i for i, n in enumerate(nombres) if n.startswith("Publicar la imagen")
        )
        assert indice_verificacion < indice_publicacion
        assert "VERSION" in pasos[indice_verificacion]["run"]
        assert pasos[indice_verificacion]["if"] == "startsWith(github.ref, 'refs/tags/v')"

    def test_la_release_solo_se_crea_en_tags_con_permiso_de_escritura_acotado(self) -> None:
        flujo = yaml.safe_load(
            (RAIZ / ".github" / "workflows" / "cd.yml").read_text(encoding="utf-8")
        )
        release = flujo["jobs"]["release"]

        assert release["if"] == "startsWith(github.ref, 'refs/tags/v')"
        assert release["needs"] == "build-and-deploy"
        assert release["permissions"] == {"contents": "write"}
        assert flujo["jobs"]["build-and-deploy"]["permissions"]["contents"] == "read"
