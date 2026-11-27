"""`US-12.2.5` (`IM-05`): el verificador de vencimientos corre en un solo proceso a la vez.

Cada corrida toma un bloqueo consultivo de PostgreSQL; si otro proceso ya lo tiene, la corrida se salta.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

import src.app as app_modulo
from src.app import CLAVE_BLOQUEO_VERIFICADOR, ejecutar_corrida_del_verificador
from src.shared.frameworks.db import SessionLocal


class _CasoDeUsoFalso:
    def __init__(self, corridas: list[str]) -> None:
        self._corridas = corridas

    async def execute(self) -> None:
        self._corridas.append("corrida")


@pytest.fixture
def corridas(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    registro: list[str] = []
    monkeypatch.setattr(
        app_modulo,
        "build_verificar_vencimientos_use_case",
        lambda _session: _CasoDeUsoFalso(registro),
    )
    return registro


async def test_sin_otro_proceso_la_corrida_se_ejecuta(corridas: list[str]) -> None:
    ejecutada = await ejecutar_corrida_del_verificador()

    assert ejecutada is True
    assert corridas == ["corrida"]


async def test_con_el_bloqueo_tomado_por_otro_proceso_la_corrida_se_salta(
    corridas: list[str],
) -> None:
    async with SessionLocal() as otro_proceso:
        resultado = await otro_proceso.execute(
            text("SELECT pg_try_advisory_xact_lock(:clave)"), {"clave": CLAVE_BLOQUEO_VERIFICADOR}
        )
        assert resultado.scalar_one() is True

        ejecutada = await ejecutar_corrida_del_verificador()

        assert ejecutada is False
        assert corridas == []

    # Cuando el otro proceso termina su transacción, la siguiente corrida sí se ejecuta.
    assert await ejecutar_corrida_del_verificador() is True
    assert corridas == ["corrida"]


async def test_el_bloqueo_se_suelta_al_terminar_la_corrida(corridas: list[str]) -> None:
    await ejecutar_corrida_del_verificador()

    async with SessionLocal() as otra_sesion:
        resultado = await otra_sesion.execute(
            text("SELECT pg_try_advisory_xact_lock(:clave)"), {"clave": CLAVE_BLOQUEO_VERIFICADOR}
        )
        assert resultado.scalar_one() is True


async def test_si_el_caso_de_uso_falla_el_bloqueo_tambien_se_suelta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Roto:
        async def execute(self) -> None:
            raise RuntimeError("falla técnica")

    monkeypatch.setattr(app_modulo, "build_verificar_vencimientos_use_case", lambda _s: _Roto())

    with pytest.raises(RuntimeError):
        await ejecutar_corrida_del_verificador()

    async with SessionLocal() as otra_sesion:
        resultado = await otra_sesion.execute(
            text("SELECT pg_try_advisory_xact_lock(:clave)"), {"clave": CLAVE_BLOQUEO_VERIFICADOR}
        )
        assert resultado.scalar_one() is True
