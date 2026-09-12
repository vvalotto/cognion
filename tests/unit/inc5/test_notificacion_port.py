"""Tests unitarios del contrato `NotificacionPort` de Actividad Evaluativa (US-5.1.1).

Sin adapter ni consumidor todavía — se cablea en `US-5.1.2`. Este test solo verifica que el
contrato queda declarado como puerto abstracto.
"""

import pytest

from src.actividad_evaluativa.entities.ports.notificacion_port import NotificacionPort


class TestNotificacionPort:
    def test_es_abstracto_no_instanciable(self):
        with pytest.raises(TypeError):
            NotificacionPort()  # type: ignore[abstract]
