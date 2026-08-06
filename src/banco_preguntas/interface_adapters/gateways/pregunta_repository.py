"""Gateway SQLAlchemy que implementa `PreguntaRepositoryPort`."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.frameworks.db.models import PreguntaPlantillaModel

TIPO_OPCION_MULTIPLE = "opcion_multiple"


class SQLAlchemyPreguntaRepository(PreguntaRepositoryPort):
    """Persiste plantillas de pregunta usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def guardar(self, pregunta: PreguntaPlantillaOpcionMultiple) -> None:
        """Guarda una pregunta de opción múltiple nueva."""
        self._session.add(
            PreguntaPlantillaModel(
                id=pregunta.id,
                banco_id=pregunta.banco_id,
                tipo=TIPO_OPCION_MULTIPLE,
                texto=pregunta.texto,
                opciones=[
                    {"texto": opcion.texto, "es_correcta": opcion.es_correcta}
                    for opcion in pregunta.opciones
                ],
                unidad_tematica=pregunta.unidad_tematica,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad.value,
                importancia=pregunta.importancia.value,
                activa=pregunta.activa,
            )
        )
        await self._session.commit()
