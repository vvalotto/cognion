"""Tests unitarios del puerto `CanalEnvioPort` (US-5.1.1)."""

import pytest

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort


class TestCanalEnvioPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            CanalEnvioPort()  # type: ignore[abstract]
