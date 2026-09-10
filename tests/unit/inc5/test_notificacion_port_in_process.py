"""Tests unitarios de `NotificacionPortInProcess` (US-5.1.2, US-5.1.3).

Reemplaza `_notificar_apertura_use_case`/`_notificar_cierre_use_case` por dobles en memoria
después de construir el adapter — evita tocar la base de datos real (mismo criterio que
`tests/unit/inc5/test_comision_consulta_port_in_process.py` para adapters in-process que
envuelven dependencias con sesión real).
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from src.actividad_evaluativa.frameworks.adapters.notificacion_port_in_process import (
    NotificacionPortInProcess,
)


class _FakeNotificarUseCase:
    def __init__(self) -> None:
        self.llamadas: list[tuple] = []

    async def execute(self, *args):
        self.llamadas.append(args)


def _construir_adapter() -> (
    tuple[NotificacionPortInProcess, _FakeNotificarUseCase, _FakeNotificarUseCase]
):
    adapter = NotificacionPortInProcess(MagicMock())
    fake_apertura = _FakeNotificarUseCase()
    fake_cierre = _FakeNotificarUseCase()
    adapter._notificar_apertura_use_case = fake_apertura  # type: ignore[attr-defined]
    adapter._notificar_cierre_use_case = fake_cierre  # type: ignore[attr-defined]
    return adapter, fake_apertura, fake_cierre


class TestNotificacionPortInProcess:
    async def test_notificar_apertura_delega_en_el_use_case_de_notificaciones(self):
        adapter, fake_apertura, _fake_cierre = _construir_adapter()
        actividad_id, materia_id = uuid4(), uuid4()
        apertura = datetime.now(UTC)
        cierre = apertura + timedelta(days=7)
        comisiones_ids = [uuid4()]

        await adapter.notificar_apertura(
            actividad_id,
            materia_id,
            "Ingeniería de Software",
            "Parcial 1",
            apertura,
            cierre,
            comisiones_ids,
        )

        assert fake_apertura.llamadas == [
            (
                actividad_id,
                materia_id,
                "Ingeniería de Software",
                "Parcial 1",
                apertura,
                cierre,
                comisiones_ids,
            )
        ]

    async def test_notificar_cierre_delega_en_el_use_case_de_notificaciones(self):
        adapter, _fake_apertura, fake_cierre = _construir_adapter()
        actividad_id, materia_id = uuid4(), uuid4()
        comisiones_ids = [uuid4()]

        await adapter.notificar_cierre(
            actividad_id,
            materia_id,
            "Ingeniería de Software",
            "Parcial 1",
            comisiones_ids,
        )

        assert fake_cierre.llamadas == [
            (
                actividad_id,
                materia_id,
                "Ingeniería de Software",
                "Parcial 1",
                comisiones_ids,
            )
        ]
