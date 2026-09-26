"""Rechazo de `opcion_indice` negativo en el borde HTTP (revisión manual 2026-09-26)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.actividad_evaluativa.frameworks.api.schemas import (
    RegistrarRespuestaRequest,
    ResponderEnVivoRequest,
)


@pytest.mark.parametrize("schema", [RegistrarRespuestaRequest, ResponderEnVivoRequest])
def test_rechaza_opcion_indice_negativo(schema: type) -> None:
    """Un índice de opción negativo nunca es una opción válida: 422."""
    with pytest.raises(ValidationError, match="no puede ser negativo"):
        schema(pregunta_id=uuid4(), contenido={"opcion_indice": -1})


@pytest.mark.parametrize("schema", [RegistrarRespuestaRequest, ResponderEnVivoRequest])
def test_acepta_opcion_indice_cero(schema: type) -> None:
    """El índice 0 (primera opción) es válido."""
    assert schema(pregunta_id=uuid4(), contenido={"opcion_indice": 0}).contenido == {
        "opcion_indice": 0
    }


def test_periodo_abierto_sigue_aceptando_valor_booleano() -> None:
    """Verdadero/Falso no se ve afectado por la validación del índice."""
    request = RegistrarRespuestaRequest(pregunta_id=uuid4(), contenido={"valor": False})
    assert request.contenido == {"valor": False}
