"""Estructura de `deploy/servidor/`, `preparar-env.sh`, la guía y el paquete (US-10.2.2, escenarios 1 a 4, 11 y 12)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest
import yaml

from tests.unit.inc10._servidor import RAIZ, SERVIDOR

GCP = RAIZ / "deploy" / "gcp"
GUIA = RAIZ / "docs" / "INSTALACION.md"


def _archivos_del_servidor() -> list[Path]:
    return sorted(p for p in SERVIDOR.iterdir() if p.is_file())


class TestSinDependenciaDeGoogle:
    """Escenario 1."""

    @pytest.mark.parametrize("archivo", _archivos_del_servidor(), ids=lambda p: p.name)
    def test_ningun_archivo_menciona_gcloud(self, archivo: Path) -> None:
        assert "gcloud" not in archivo.read_text(encoding="utf-8")

    def test_no_se_copiaron_los_scripts_de_gcp(self) -> None:
        nombres = {p.name for p in _archivos_del_servidor()}

        assert not nombres & {"aprovisionar.sh", "destruir.sh", "desplegar.sh", "preparar-vm.sh"}

    def test_los_scripts_son_ejecutables_y_tienen_sintaxis_valida(self) -> None:
        for script in SERVIDOR.glob("*.sh"):
            assert script.stat().st_mode & 0o111, f"{script.name} no es ejecutable"
            assert subprocess.run(["bash", "-n", str(script)], check=False).returncode == 0

    def test_caddyfile_y_salud_son_iguales_a_los_de_gcp(self) -> None:
        for nombre in ("Caddyfile", "salud.sh"):
            assert (SERVIDOR / nombre).read_text() == (GCP / nombre).read_text(), nombre


class TestComposicion:
    """Escenario 2."""

    @pytest.fixture
    def compose(self) -> dict:
        return yaml.safe_load((SERVIDOR / "docker-compose.yml").read_text(encoding="utf-8"))

    def test_define_base_aplicacion_y_proxy(self, compose: dict) -> None:
        assert set(compose["services"]) == {"db", "app", "caddy"}

    def test_solo_caddy_publica_puertos(self, compose: dict) -> None:
        publican = [n for n, s in compose["services"].items() if "ports" in s]

        assert publican == ["caddy"]

    def test_los_puertos_son_configurables_con_80_y_443_por_defecto(self, compose: dict) -> None:
        assert compose["services"]["caddy"]["ports"] == [
            "${COGNION_HTTP_PORT:-80}:80",
            "${COGNION_HTTPS_PORT:-443}:443",
        ]

    def test_la_memoria_es_configurable_y_no_esta_fijada_para_1gb(self, compose: dict) -> None:
        assert compose["services"]["db"]["mem_limit"] == "${COGNION_MEM_DB:-1g}"
        assert compose["services"]["app"]["mem_limit"] == "${COGNION_MEM_APP:-1g}"

    def test_la_aplicacion_espera_a_la_base_y_usa_la_imagen_del_env(self, compose: dict) -> None:
        app = compose["services"]["app"]

        assert app["image"] == "${COGNION_IMAGE}"
        assert app["depends_on"]["db"]["condition"] == "service_healthy"

    def test_postgres_conserva_max_connections_para_una_clase_completa(self, compose: dict) -> None:
        assert "max_connections=100" in compose["services"]["db"]["command"]


class TestEnvExample:
    """Los marcadores que reemplaza `preparar-env.sh`."""

    def test_tiene_todos_los_marcadores_y_claves(self) -> None:
        texto = (SERVIDOR / ".env.example").read_text(encoding="utf-8")

        for marcador in ("__DOMINIO__", "__IMAGEN__", "__URL__", "__SECRETO__", "__PASSWORD_DB__"):
            assert marcador in texto
        for clave in (
            "ENTORNO=local",
            "EMAIL_MODO=consola",
            "FRONTEND_URL=",
            "CORS_ALLOWED_ORIGINS=",
        ):
            assert clave in texto


@pytest.fixture
def paquete(tmp_path: Path) -> Path:
    """Reproduce la estructura del paquete: `<raiz>/VERSION` y `<raiz>/deploy/servidor/`."""
    raiz = tmp_path / "cognion-9.9.9"
    carpeta = raiz / "deploy" / "servidor"
    carpeta.mkdir(parents=True)
    (raiz / "VERSION").write_text("9.9.9\n")
    for nombre in ("preparar-env.sh", ".env.example"):
        shutil.copy(SERVIDOR / nombre, carpeta / nombre)
    return carpeta


def _preparar_env(carpeta: Path, *args: str, **entorno: str) -> subprocess.CompletedProcess[str]:
    import os

    return subprocess.run(  # noqa: S603,S607
        ["bash", str(carpeta / "preparar-env.sh"), *args],
        capture_output=True,
        text=True,
        input="",
        env={**os.environ, **entorno},
        check=False,
    )


def _leer(carpeta: Path) -> dict[str, str]:
    lineas = (carpeta / ".env").read_text().splitlines()
    return dict(l.split("=", 1) for l in lineas if "=" in l and not l.startswith("#"))


class TestPrepararEnv:
    """Escenarios 3 y 4."""

    def test_crea_el_env_con_permisos_600_dominio_e_imagen_de_la_version(
        self, paquete: Path
    ) -> None:
        r = _preparar_env(paquete, "cognion.facultad.edu.ar")

        assert r.returncode == 0, r.stderr
        env = _leer(paquete)
        assert (paquete / ".env").stat().st_mode & 0o777 == 0o600
        assert env["COGNION_DOMINIO"] == "cognion.facultad.edu.ar"
        assert env["COGNION_IMAGE"] == "ghcr.io/vvalotto/cognion:v9.9.9"
        assert env["FRONTEND_URL"] == "https://cognion.facultad.edu.ar"
        assert env["CORS_ALLOWED_ORIGINS"] == "https://cognion.facultad.edu.ar"
        assert not re.search(r"__[A-Z_]+__", (paquete / ".env").read_text())

    def test_los_secretos_son_aleatorios_y_distintos_en_cada_instalacion(
        self, paquete: Path, tmp_path: Path
    ) -> None:
        _preparar_env(paquete, "uno.edu.ar")
        otro = tmp_path / "otro" / "deploy" / "servidor"
        shutil.copytree(paquete.parent.parent, otro.parent.parent)
        (otro / ".env").unlink()
        _preparar_env(otro, "uno.edu.ar")

        a, b = _leer(paquete), _leer(otro)
        assert len(a["SECRET_KEY"]) == 64 and a["SECRET_KEY"] != b["SECRET_KEY"]
        assert a["POSTGRES_PASSWORD"] != b["POSTGRES_PASSWORD"]
        assert a["POSTGRES_PASSWORD"] in a["DATABASE_URL"]

    def test_no_pisa_un_env_existente(self, paquete: Path) -> None:
        (paquete / ".env").write_text("COGNION_DOMINIO=el.de.antes\n")

        r = _preparar_env(paquete, "nuevo.edu.ar")

        assert r.returncode == 0 and "ya existe" in r.stdout
        assert (paquete / ".env").read_text() == "COGNION_DOMINIO=el.de.antes\n"

    @pytest.mark.parametrize(
        "invalido", ["https://x.edu.ar", "x.edu.ar/ruta", "con espacio", "x.edu.ar:8080"]
    )
    def test_rechaza_un_dominio_invalido(self, paquete: Path, invalido: str) -> None:
        r = _preparar_env(paquete, invalido)

        assert r.returncode != 0
        assert not (paquete / ".env").exists()

    def test_falla_si_no_encuentra_el_archivo_version(self, paquete: Path) -> None:
        (paquete.parent.parent / "VERSION").unlink()

        r = _preparar_env(paquete, "x.edu.ar")

        assert r.returncode != 0 and "VERSION" in r.stderr

    def test_sin_dominio_usa_http_en_el_puerto_80(self, paquete: Path) -> None:
        r = _preparar_env(paquete, "--sin-dominio", "10.0.0.15")

        assert r.returncode == 0, r.stderr
        env = _leer(paquete)
        assert env["COGNION_DOMINIO"] == ":80"
        assert env["FRONTEND_URL"] == "http://10.0.0.15"
        assert "COGNION_HTTP_PORT" not in env

    def test_sin_dominio_con_otro_puerto_lo_incluye_en_la_url_y_en_el_env(
        self, paquete: Path
    ) -> None:
        r = _preparar_env(paquete, "--sin-dominio", "10.0.0.15", COGNION_HTTP_PORT="8080")

        assert r.returncode == 0, r.stderr
        env = _leer(paquete)
        assert env["FRONTEND_URL"] == "http://10.0.0.15:8080"
        assert env["CORS_ALLOWED_ORIGINS"] == "http://10.0.0.15:8080"
        assert env["COGNION_HTTP_PORT"] == "8080"


class TestGuia:
    """Escenario 11."""

    SECCIONES = (
        "Qué camino elegir",
        "Camino A",
        "Camino B",
        "Camino C",
        "Actualizar y volver atrás",
        "Respaldo y restauración",
        "dirección correcta",
        "Limitaciones conocidas",
        "Problemas frecuentes",
    )

    def test_tiene_las_secciones_pedidas(self) -> None:
        texto = GUIA.read_text(encoding="utf-8")

        for seccion in self.SECCIONES:
            assert seccion in texto, seccion

    def test_cada_subcomando_de_cognion_sh_que_menciona_existe(self) -> None:
        guia = GUIA.read_text(encoding="utf-8")
        script = (SERVIDOR / "cognion.sh").read_text(encoding="utf-8")
        mencionados = set(re.findall(r"\./cognion\.sh ([a-z]+)", guia))

        assert {
            "iniciar",
            "administrador",
            "estado",
            "respaldar",
            "restaurar",
            "desplegar",
            "rollback",
            "email",
        } <= mencionados
        for sub in mencionados:
            assert re.search(
                rf"^\s+{sub}\)", script, re.MULTILINE
            ), f"cognion.sh no tiene el subcomando {sub}"

    def test_las_ordenes_de_scripts_que_menciona_existen(self) -> None:
        guia = GUIA.read_text(encoding="utf-8")

        for ruta in set(re.findall(r"(scripts/local/[a-z_]+\.sh)", guia)):
            assert (RAIZ / ruta).exists(), ruta
        for script in set(re.findall(r"\./([a-z-]+\.sh)", guia)):
            assert (SERVIDOR / script).exists(), script


class TestPaquete:
    """Escenario 12: el paquete de la release lleva el servidor y la guía."""

    def test_el_paquete_incluye_deploy_servidor_y_la_guia(self, tmp_path: Path) -> None:
        version = (RAIZ / "VERSION").read_text().strip()
        r = subprocess.run(  # noqa: S603,S607
            ["bash", str(RAIZ / "scripts" / "empaquetar_release.sh"), version],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", "SALIDA": str(tmp_path)},
            check=False,
        )

        assert r.returncode == 0, r.stderr
        with tarfile.open(tmp_path / f"cognion-{version}-instalacion.tar.gz") as tar:
            nombres = set(tar.getnames())
        base = f"cognion-{version}"
        for esperado in (
            "docs/INSTALACION.md",
            "deploy/servidor/cognion.sh",
            "deploy/servidor/docker-compose.yml",
            "deploy/servidor/respaldar.sh",
            "deploy/servidor/restaurar.sh",
            "deploy/servidor/.env.example",
        ):
            assert f"{base}/{esperado}" in nombres, esperado
