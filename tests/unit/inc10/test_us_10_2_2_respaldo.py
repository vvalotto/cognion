"""`respaldar.sh` y `restaurar.sh` con `docker` simulado (US-10.2.2, escenarios 7, 8 y 10)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from tests.unit.inc10._servidor import correr, log, preparar


def _dumps(carpeta: Path) -> list[Path]:
    return sorted((carpeta / "respaldos").glob("cognion-*.dump"))


class TestRespaldar:
    """Escenarios 7 y 8."""

    def test_genera_el_dump_y_su_sha256(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "respaldar.sh")

        assert r.returncode == 0, r.stderr
        (dump,) = _dumps(carpeta)
        esperado = hashlib.sha256(dump.read_bytes()).hexdigest()
        assert (dump.parent / f"{dump.name}.sha256").read_text().split()[0] == esperado
        assert not list(dump.parent.glob("*.parcial*"))

    def test_verifica_que_el_archivo_sea_legible_antes_de_darlo_por_bueno(
        self, tmp_path: Path
    ) -> None:
        carpeta = preparar(tmp_path)

        correr(tmp_path, carpeta, "respaldar.sh")

        assert any(l.startswith("EXEC pg_restore --list") for l in log(tmp_path))

    def test_conserva_solo_los_ultimos_n_y_borra_tambien_sus_hashes(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        destino = carpeta / "respaldos"
        destino.mkdir()
        for fecha in ("20200101-000000", "20200102-000000", "20200103-000000"):
            (destino / f"cognion-{fecha}.dump").write_bytes(b"PGDMP-viejo")
            (destino / f"cognion-{fecha}.dump.sha256").write_text("x")

        r = correr(tmp_path, carpeta, "respaldar.sh", COGNION_RESPALDOS_N=2)

        assert r.returncode == 0, r.stderr
        nombres = [p.name for p in _dumps(carpeta)]
        assert len(nombres) == 2
        assert (
            "cognion-20200103-000000.dump" in nombres
            and "cognion-20200101-000000.dump" not in nombres
        )
        assert not (destino / "cognion-20200101-000000.dump.sha256").exists()

    def test_la_carpeta_destino_se_puede_elegir(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        otra = tmp_path / "otra"

        r = correr(tmp_path, carpeta, "respaldar.sh", COGNION_RESPALDOS=otra)

        assert r.returncode == 0, r.stderr
        assert list(otra.glob("cognion-*.dump"))

    def test_rechaza_una_cantidad_a_conservar_invalida(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        for invalido in ("0", "-1", "abc"):
            r = correr(tmp_path, carpeta, "respaldar.sh", COGNION_RESPALDOS_N=invalido)
            assert r.returncode != 0, invalido

    def test_si_pg_dump_falla_no_queda_ningun_archivo(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, pg_dump_falla=True)

        r = correr(tmp_path, carpeta, "respaldar.sh")

        assert r.returncode != 0
        assert "pg_dump falló" in r.stderr
        assert list((carpeta / "respaldos").iterdir()) == []

    def test_si_el_dump_sale_vacio_se_descarta(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, dump_vacio=True)

        r = correr(tmp_path, carpeta, "respaldar.sh")

        assert r.returncode != 0
        assert list((carpeta / "respaldos").iterdir()) == []

    def test_si_el_dump_no_es_legible_se_descarta(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, dump_ilegible=True)

        r = correr(tmp_path, carpeta, "respaldar.sh")

        assert r.returncode != 0
        assert "no es legible" in r.stderr
        assert list((carpeta / "respaldos").iterdir()) == []

    def test_sin_docker_falla_con_mensaje_claro(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, con_docker=False)

        r = correr(tmp_path, carpeta, "respaldar.sh")

        assert r.returncode != 0 and "Falta docker" in r.stderr


def _respaldo_valido(tmp_path: Path, carpeta: Path) -> Path:
    correr(tmp_path, carpeta, "respaldar.sh")
    (dump,) = _dumps(carpeta)
    return dump


class TestRestaurar:
    """Escenario 10."""

    def test_rechaza_un_archivo_cuyo_hash_no_coincide_sin_tocar_nada(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        dump = _respaldo_valido(tmp_path, carpeta)
        dump.write_bytes(dump.read_bytes() + b"corrupto")
        (tmp_path / "llamadas.log").unlink()

        r = correr(tmp_path, carpeta, "restaurar.sh", str(dump))

        assert r.returncode != 0
        assert "sha256" in r.stderr
        assert log(tmp_path) == []

    def test_rechaza_un_archivo_ilegible(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, dump_ilegible=True)
        archivo = tmp_path / "x.dump"
        archivo.write_bytes(b"PGDMP-FALSO\n")

        r = correr(tmp_path, carpeta, "restaurar.sh", str(archivo))

        assert r.returncode != 0 and "legible" in r.stderr

    def test_pide_el_archivo(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)

        r = correr(tmp_path, carpeta, "restaurar.sh")

        assert r.returncode != 0 and "Indicá el archivo" in r.stderr

    def test_el_ensayo_usa_una_base_temporal_y_no_toca_la_real(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        dump = _respaldo_valido(tmp_path, carpeta)
        (tmp_path / "llamadas.log").unlink()

        r = correr(tmp_path, carpeta, "restaurar.sh", str(dump))

        assert r.returncode == 0, r.stderr
        llamadas = log(tmp_path)
        assert any(l.startswith("EXEC createdb -U cognion cognion_ensayo_") for l in llamadas)
        assert any(
            l.startswith("EXEC dropdb -U cognion --if-exists cognion_ensayo_") for l in llamadas
        )
        restauraciones = [
            l for l in llamadas if l.startswith("EXEC pg_restore") and "--list" not in l
        ]
        assert len(restauraciones) == 1 and "-d cognion_ensayo_" in restauraciones[0]
        assert not any(l.startswith("STOP") for l in llamadas)
        assert (
            "Ensayo OK" in r.stdout
            and "Tablas restauradas: 40" in r.stdout
            and "base actual: 42" in r.stdout
        )

    def test_si_el_ensayo_falla_borra_igual_la_base_temporal(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path, restauracion_falla=True)
        archivo = tmp_path / "x.dump"
        archivo.write_bytes(b"PGDMP-FALSO\n")

        r = correr(tmp_path, carpeta, "restaurar.sh", str(archivo))

        assert r.returncode != 0 and "La base real no se tocó" in r.stderr
        assert any(l.startswith("EXEC dropdb") for l in log(tmp_path))

    def test_reemplazar_sin_confirmar_no_hace_nada(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        dump = _respaldo_valido(tmp_path, carpeta)
        (tmp_path / "llamadas.log").unlink()

        r = correr(tmp_path, carpeta, "restaurar.sh", str(dump), "--reemplazar", entrada="no\n")

        assert r.returncode != 0 and "Cancelado" in r.stdout
        assert not any(l.startswith(("STOP", "EXEC pg_restore --clean")) for l in log(tmp_path))

    def test_reemplazar_confirmando_detiene_restaura_en_una_transaccion_y_levanta(
        self, tmp_path: Path
    ) -> None:
        carpeta = preparar(tmp_path)
        dump = _respaldo_valido(tmp_path, carpeta)
        (tmp_path / "llamadas.log").unlink()

        r = correr(
            tmp_path, carpeta, "restaurar.sh", str(dump), "--reemplazar", entrada="RESTAURAR\n"
        )

        assert r.returncode == 0, r.stderr
        llamadas = log(tmp_path)
        parar = llamadas.index("STOP app")
        restaurar = next(
            i for i, l in enumerate(llamadas) if l.startswith("EXEC pg_restore --clean")
        )
        levantar = next(i for i, l in enumerate(llamadas) if l.startswith("UP_APP"))
        assert parar < restaurar < levantar
        assert "--single-transaction" in llamadas[restaurar] and "-d cognion" in llamadas[restaurar]

    def test_si_la_restauracion_falla_levanta_la_aplicacion_y_avisa(self, tmp_path: Path) -> None:
        carpeta = preparar(tmp_path)
        dump = _respaldo_valido(tmp_path, carpeta)
        (tmp_path / "estado.json").write_text('{"restauracion_falla": true}')

        r = correr(
            tmp_path, carpeta, "restaurar.sh", str(dump), "--reemplazar", entrada="RESTAURAR\n"
        )

        assert r.returncode != 0
        assert "una sola transacción" in r.stderr
        assert any(l.startswith("UP_APP") for l in log(tmp_path))
