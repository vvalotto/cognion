"""Tests unitarios del puerto y DTO de `ComisionConsultaPort` de Notificaciones (US-5.1.1)."""

from uuid import uuid4

import pytest

from src.notificaciones.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    DestinatarioNotificacion,
)


class TestDestinatarioNotificacion:
    def test_es_inmutable(self):
        destinatario = DestinatarioNotificacion(
            estudiante_id=uuid4(), nombre="Ana Pérez", email="ana@fiuner.edu.ar"
        )

        with pytest.raises(AttributeError):
            destinatario.email = "otro@fiuner.edu.ar"  # type: ignore[misc]

    def test_conserva_los_valores_recibidos(self):
        estudiante_id = uuid4()
        destinatario = DestinatarioNotificacion(
            estudiante_id=estudiante_id, nombre="Ana Pérez", email="ana@fiuner.edu.ar"
        )

        assert destinatario.estudiante_id == estudiante_id
        assert destinatario.nombre == "Ana Pérez"
        assert destinatario.email == "ana@fiuner.edu.ar"


class TestComisionConsultaPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            ComisionConsultaPort()  # type: ignore[abstract]
