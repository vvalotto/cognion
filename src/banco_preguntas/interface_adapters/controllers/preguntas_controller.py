"""Controller de la API para operaciones sobre preguntas."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)


class PreguntasController:
    """Adapta requests HTTP a los casos de uso de gestión de preguntas."""

    def __init__(
        self, cargar_pregunta_opcion_multiple: CargarPreguntaOpcionMultipleUseCase
    ) -> None:
        """Recibe el caso de uso de carga de pregunta de opción múltiple."""
        self._cargar_pregunta_opcion_multiple = cargar_pregunta_opcion_multiple

    async def cargar_pregunta_opcion_multiple(
        self,
        banco_id: UUID,
        texto: str,
        opciones: list[Opcion],
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> tuple[PreguntaPlantillaOpcionMultiple, PreguntaCargada]:
        """Delega la carga de la pregunta en el caso de uso correspondiente."""
        return await self._cargar_pregunta_opcion_multiple.execute(
            banco_id=banco_id,
            texto=texto,
            opciones=opciones,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )
