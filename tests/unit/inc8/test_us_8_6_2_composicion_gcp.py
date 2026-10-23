"""Composición de la VM de la prueba en GCP: validación estática (US-8.6.2, ADR-025).

La verificación de runtime (arranque real, memoria, reinicio) corre en CI y en la VM con
`tests/uat/inc8/verificar_composicion_gcp.sh`; acá se comprueba que la configuración declara lo que debe.
"""

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]
GCP = RAIZ / "deploy" / "gcp"
SERVICIOS = ("db", "app", "caddy")


@pytest.fixture(scope="module")
def compose() -> dict:
    """Composición ya parseada."""
    return yaml.safe_load((GCP / "docker-compose.yml").read_text())


def test_define_los_tres_servicios(compose: dict) -> None:
    """Base, aplicación y proxy HTTPS."""
    assert set(compose["services"]) == set(SERVICIOS)


@pytest.mark.parametrize("servicio", SERVICIOS)
def test_cada_servicio_tiene_limite_de_memoria_y_reinicio(compose: dict, servicio: str) -> None:
    """Techo de memoria para 1 GB y reinicio automático."""
    definicion = compose["services"][servicio]
    assert re.fullmatch(r"\d+m", str(definicion["mem_limit"]))
    assert definicion["restart"] == "unless-stopped"


@pytest.mark.parametrize("servicio", SERVICIOS)
def test_logs_con_rotacion(compose: dict, servicio: str) -> None:
    """Sin rotación el disco de 30 GB se llenaría con los logs."""
    logging = compose["services"][servicio]["logging"]
    assert logging["driver"] == "json-file"
    assert logging["options"]["max-size"] and logging["options"]["max-file"]


def test_solo_caddy_publica_puertos(compose: dict) -> None:
    """La base y la aplicación quedan en la red interna; solo 80 y 443 salen."""
    assert "ports" not in compose["services"]["db"]
    assert "ports" not in compose["services"]["app"]
    assert sorted(compose["services"]["caddy"]["ports"]) == ["443:443", "80:80"]


def test_la_aplicacion_espera_a_la_base_sana(compose: dict) -> None:
    """Sin base lista la aplicación no arranca."""
    assert compose["services"]["app"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert "healthcheck" in compose["services"]["db"]
    assert "healthcheck" in compose["services"]["app"]


def test_postgres_ajustado_para_poca_memoria(compose: dict) -> None:
    """Memoria compartida y conexiones acotadas; max_connections cubre ~60 alumnos con NullPool."""
    comando = " ".join(compose["services"]["db"]["command"])
    assert "shared_buffers=64MB" in comando
    assert "work_mem=2MB" in comando
    conexiones = int(re.search(r"max_connections=(\d+)", comando).group(1))
    assert 60 <= conexiones <= 150


def test_la_base_usa_volumen_nombrado(compose: dict) -> None:
    """Los datos sobreviven a recrear el contenedor."""
    assert "db-data" in compose["volumes"]
    assert any(v.startswith("db-data:") for v in compose["services"]["db"]["volumes"])


def test_el_proxy_solo_reenvia_a_la_aplicacion() -> None:
    """Caddy sirve el dominio de la variable y reenvía a app:8000."""
    caddyfile = (GCP / "Caddyfile").read_text()
    assert "{$COGNION_DOMINIO}" in caddyfile
    assert "reverse_proxy app:8000" in caddyfile


def _variables(texto: str) -> dict[str, str]:
    return dict(
        linea.split("=", 1) for linea in texto.splitlines() if linea and not linea.startswith("#")
    )


def test_la_plantilla_no_trae_secretos_reales() -> None:
    """Todo valor secreto es un marcador que reemplaza `preparar-env.sh`."""
    variables = _variables((GCP / ".env.example").read_text())
    assert variables["SECRET_KEY"] == "__SECRETO__"
    assert variables["POSTGRES_PASSWORD"] == "__PASSWORD_DB__"
    assert "__PASSWORD_DB__" in variables["DATABASE_URL"]
    assert not re.search(r"[0-9a-f]{32,}", (GCP / ".env.example").read_text())


def test_la_plantilla_aplica_las_decisiones_del_adr() -> None:
    """ADR-025: `ENTORNO=local`, emails en el log y base en el servicio `db`."""
    variables = _variables((GCP / ".env.example").read_text())
    assert variables["ENTORNO"] == "local"
    assert variables["EMAIL_MODO"] == "consola"
    assert "@db:5432/" in variables["DATABASE_URL"]
    assert variables["FRONTEND_URL"].startswith("https://")


def test_el_dockerfile_no_arranca_con_uv_run() -> None:
    """`uv run` al arrancar podría sincronizar dependencias (ADR-025, decisión 3)."""
    dockerfile = (RAIZ / "Dockerfile").read_text()
    cmd = next(linea for linea in dockerfile.splitlines() if linea.startswith("CMD"))
    assert '"uv"' not in cmd  # el ejecutable `uv`, no `uvicorn`
    assert cmd.startswith('CMD ["uvicorn"')
    assert "/app/.venv/bin:$PATH" in dockerfile


def test_la_aplicacion_no_migra_al_arrancar() -> None:
    """Las migraciones son un paso explícito (US-8.1.4): el arranque no las invoca."""
    dockerfile = (RAIZ / "Dockerfile").read_text()
    cmd = next(linea for linea in dockerfile.splitlines() if linea.startswith("CMD"))
    assert "alembic" not in cmd
    assert "alembic upgrade head" in (GCP / "cognion.sh").read_text()


def test_los_scripts_son_ejecutables() -> None:
    """`preparar-env.sh` y `cognion.sh` se ejecutan directo."""
    for nombre in ("preparar-env.sh", "cognion.sh"):
        assert (GCP / nombre).stat().st_mode & stat.S_IXUSR


def _preparar(tmp_path: Path, *argumentos: str) -> subprocess.CompletedProcess[str]:
    carpeta = tmp_path / "gcp"
    carpeta.mkdir(exist_ok=True)
    for nombre in ("preparar-env.sh", ".env.example"):
        destino = carpeta / nombre
        if not destino.exists():
            shutil.copy(GCP / nombre, destino)
    return subprocess.run(  # noqa: S603
        ["bash", str(carpeta / "preparar-env.sh"), *argumentos],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ},
    )


def test_preparar_env_genera_secretos_y_permisos_600(tmp_path: Path) -> None:
    """Escenario 4: secretos aleatorios, permisos 600 y sin imprimirlos."""
    resultado = _preparar(tmp_path, "cognion.duckdns.org")
    env = tmp_path / "gcp" / ".env"
    assert resultado.returncode == 0
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    variables = _variables(env.read_text())
    assert variables["COGNION_DOMINIO"] == "cognion.duckdns.org"
    assert variables["FRONTEND_URL"] == "https://cognion.duckdns.org"
    assert len(variables["SECRET_KEY"]) == 64
    assert variables["POSTGRES_PASSWORD"] in variables["DATABASE_URL"]
    assert not re.search(r"__[A-Z_]+__", env.read_text())
    assert variables["SECRET_KEY"] not in resultado.stdout + resultado.stderr
    assert variables["POSTGRES_PASSWORD"] not in resultado.stdout + resultado.stderr


def test_preparar_env_es_idempotente(tmp_path: Path) -> None:
    """Una segunda ejecución no pisa el `.env` existente."""
    _preparar(tmp_path, "cognion.duckdns.org")
    env = tmp_path / "gcp" / ".env"
    antes = env.read_text()
    resultado = _preparar(tmp_path, "otro.duckdns.org")
    assert resultado.returncode == 0
    assert env.read_text() == antes


@pytest.mark.parametrize("dominio", ["https://x.duckdns.org", "con espacio.org", "x/y.org"])
def test_preparar_env_rechaza_dominios_invalidos(tmp_path: Path, dominio: str) -> None:
    """Sin esquema, barras ni espacios; no se crea el archivo."""
    resultado = _preparar(tmp_path, dominio)
    assert resultado.returncode != 0
    assert "inválido" in resultado.stderr
    assert not (tmp_path / "gcp" / ".env").exists()


def test_la_configuracion_generada_arranca_con_settings(tmp_path: Path) -> None:
    """El `.env` generado cumple las validaciones de `ENTORNO=local` (secreto fuerte)."""
    from src.settings import Settings

    _preparar(tmp_path, "cognion.duckdns.org")
    variables = _variables((tmp_path / "gcp" / ".env").read_text())
    cfg = Settings(
        entorno=variables["ENTORNO"],
        email_modo=variables["EMAIL_MODO"],
        database_url=variables["DATABASE_URL"],
        secret_key=variables["SECRET_KEY"],
        frontend_url=variables["FRONTEND_URL"],
        cors_allowed_origins=variables["CORS_ALLOWED_ORIGINS"],
    )
    assert cfg.entorno == "local"
    assert cfg.email_modo == "consola"
