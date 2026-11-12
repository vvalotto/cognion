"""`cognion.sh` del servidor con `docker` simulado (US-10.2.2, escenarios 5, 6 y 9)."""

from __future__ import annotations

from pathlib import Path

from tests.unit.inc10._servidor import correr, leer_env, log, preparar


class TestDockerAusente:
    """Escenario 6."""

    def test_falla_con_un_mensaje_claro_si_falta_docker(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, con_docker=False)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert r.returncode != 0
        assert "Falta docker" in r.stderr

    def test_falla_con_un_mensaje_claro_si_falta_el_plugin_compose(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, sin_compose=True)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert r.returncode != 0
        assert "compose" in r.stderr

    def test_pide_preparar_el_env_si_no_existe(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        (carpeta / ".env").unlink()

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert r.returncode != 0
        assert "preparar-env.sh" in r.stderr


class TestOperacion:
    """Escenario 5."""

    def test_iniciar_levanta_la_base_migra_y_arranca_la_aplicacion(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "iniciar")

        assert r.returncode == 0, r.stderr
        llamadas = log(tmp_path)
        assert llamadas.index("UP_DB") < llamadas.index("MIGRAR imagen=cognion:vieja")
        assert "UP_APP imagen=cognion:vieja" in llamadas
        assert "https://cognion.facultad.edu.ar/api/health" in r.stdout

    def test_migrar_aplica_las_migraciones(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "migrar")

        assert r.returncode == 0
        assert "MIGRAR imagen=cognion:vieja" in log(tmp_path)

    def test_estado_con_dominio_consulta_la_salud_por_https(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert r.returncode == 0, r.stderr
        urls = [l for l in log(tmp_path) if l.startswith("CURL")]
        assert urls == [
            "CURL https://cognion.facultad.edu.ar/api/health",
            "CURL https://cognion.facultad.edu.ar/api/health/ready",
        ]

    def test_estado_sin_dominio_consulta_http_en_esta_maquina(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        (carpeta / ".env").write_text("COGNION_DOMINIO=:80\nCOGNION_IMAGE=cognion:vieja\n")

        correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "CURL http://localhost:80/api/health" in log(tmp_path)

    def test_estado_sin_dominio_respeta_el_puerto_http_configurado(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        (carpeta / ".env").write_text(
            "COGNION_DOMINIO=:80\nCOGNION_HTTP_PORT=8080\nCOGNION_IMAGE=cognion:vieja\n"
        )

        correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "CURL http://localhost:8080/api/health" in log(tmp_path)

    def test_estado_con_dominio_respeta_el_puerto_https_configurado(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, env="COGNION_HTTPS_PORT=8443\n")

        correr(tmp_path, carpeta, "cognion.sh", "estado")

        assert "CURL https://cognion.facultad.edu.ar:8443/api/health" in log(tmp_path)

    def test_rollback_vuelve_a_la_imagen_anterior(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, env="COGNION_IMAGE_ANTERIOR=cognion:anterior\n")

        r = correr(tmp_path, carpeta, "cognion.sh", "rollback")

        assert r.returncode == 0, r.stderr
        assert leer_env(carpeta)["COGNION_IMAGE"] == "cognion:anterior"

    def test_un_subcomando_desconocido_muestra_la_ayuda(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "inventado")

        assert r.returncode != 0
        assert "respaldar" in r.stdout + r.stderr


class TestDespliegueConRespaldoPrevio:
    """Escenario 9."""

    def test_respalda_antes_de_migrar(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "desplegar", "ghcr.io/vvalotto/cognion:v1.0.1")

        assert r.returncode == 0, r.stderr
        llamadas = log(tmp_path)
        respaldo = next(i for i, l in enumerate(llamadas) if l.startswith("EXEC pg_dump"))
        migracion = next(i for i, l in enumerate(llamadas) if l.startswith("MIGRAR"))
        assert respaldo < migracion
        assert leer_env(carpeta)["COGNION_IMAGE"] == "ghcr.io/vvalotto/cognion:v1.0.1"
        assert leer_env(carpeta)["COGNION_IMAGE_ANTERIOR"] == "cognion:vieja"

    def test_si_el_respaldo_falla_no_se_toca_nada(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, pg_dump_falla=True)

        r = correr(tmp_path, carpeta, "cognion.sh", "desplegar", "ghcr.io/vvalotto/cognion:v1.0.1")

        assert r.returncode != 0
        assert "respaldo previo falló" in r.stderr
        assert not any(l.startswith("MIGRAR") for l in log(tmp_path))
        assert leer_env(carpeta)["COGNION_IMAGE"] == "cognion:vieja"

    def test_el_subcomando_respaldar_ejecuta_el_script(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "cognion.sh", "respaldar")

        assert r.returncode == 0, r.stderr
        assert list((carpeta / "respaldos").glob("cognion-*.dump"))
