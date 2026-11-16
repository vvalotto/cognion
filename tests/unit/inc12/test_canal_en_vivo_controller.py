"""`CanalEnVivoController` delega la decisión en el caso de uso de autorización (US-12.1.1)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.interface_adapters.controllers.canal_en_vivo_controller import (
    CanalEnVivoController,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class _CasoDeUsoFalso:
    """Registra la llamada y devuelve la decisión precargada."""

    def __init__(self, decision: bool) -> None:
        self.decision = decision
        self.llamadas: list[tuple] = []

    async def execute(self, sesion_id, usuario_id, rol) -> bool:
        self.llamadas.append((sesion_id, usuario_id, rol))
        return self.decision


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", [True, False])
async def test_delega_en_el_caso_de_uso_y_devuelve_su_decision(decision):
    """La respuesta es la del caso de uso, con los mismos argumentos."""
    caso_de_uso = _CasoDeUsoFalso(decision)
    sesion_id, usuario_id = uuid4(), uuid4()

    resultado = await CanalEnVivoController(caso_de_uso).puede_conectar(
        sesion_id, usuario_id, TipoPerfil.DOCENTE
    )

    assert resultado is decision
    assert caso_de_uso.llamadas == [(sesion_id, usuario_id, TipoPerfil.DOCENTE)]
