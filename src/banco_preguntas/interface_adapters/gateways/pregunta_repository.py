"""Gateway SQLAlchemy que implementa `PreguntaRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.frameworks.db.models import PreguntaPlantillaModel

TIPO_OPCION_MULTIPLE = "opcion_multiple"
TIPO_VERDADERO_FALSO = "verdadero_falso"


class SQLAlchemyPreguntaRepository(PreguntaRepositoryPort):
    """Persiste plantillas de pregunta usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Guarda una pregunta nueva, mapeando al modelo según su tipo concreto."""
        if isinstance(pregunta, PreguntaPlantillaVerdaderoFalso):
            modelo = PreguntaPlantillaModel(
                id=pregunta.id,
                banco_id=pregunta.banco_id,
                tipo=TIPO_VERDADERO_FALSO,
                texto=pregunta.texto,
                opciones=None,
                respuesta_correcta=pregunta.respuesta_correcta,
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad.value,
                importancia=pregunta.importancia.value,
                activa=pregunta.activa,
            )
        else:
            modelo = PreguntaPlantillaModel(
                id=pregunta.id,
                banco_id=pregunta.banco_id,
                tipo=TIPO_OPCION_MULTIPLE,
                texto=pregunta.texto,
                opciones=[
                    {"texto": opcion.texto, "es_correcta": opcion.es_correcta}
                    for opcion in pregunta.opciones
                ],
                respuesta_correcta=None,
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad.value,
                importancia=pregunta.importancia.value,
                activa=pregunta.activa,
            )

        self._session.add(modelo)
        await self._session.commit()
