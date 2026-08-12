"""Controller de la API para operaciones sobre preguntas."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.eventos import PreguntaCargada, PreguntaEditada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase


class PreguntasController:
    """Adapta requests HTTP a los casos de uso de gestión de preguntas."""

    def __init__(
        self,
        cargar_pregunta_opcion_multiple: CargarPreguntaOpcionMultipleUseCase,
        cargar_pregunta_verdadero_falso: CargarPreguntaVerdaderoFalsoUseCase,
        editar_pregunta: EditarPreguntaUseCase,
    ) -> None:
        """Recibe los casos de uso de carga (uno por tipo) y edición de pregunta."""
        self._cargar_pregunta_opcion_multiple = cargar_pregunta_opcion_multiple
        self._cargar_pregunta_verdadero_falso = cargar_pregunta_verdadero_falso
        self._editar_pregunta = editar_pregunta

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

    async def cargar_pregunta_verdadero_falso(
        self,
        banco_id: UUID,
        texto: str,
        respuesta_correcta: bool,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> tuple[PreguntaPlantillaVerdaderoFalso, PreguntaCargada]:
        """Delega la carga de la pregunta Verdadero/Falso en el caso de uso correspondiente."""
        return await self._cargar_pregunta_verdadero_falso.execute(
            banco_id=banco_id,
            texto=texto,
            respuesta_correcta=respuesta_correcta,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )

    async def editar_pregunta(
        self,
        pregunta_id: UUID,
        texto: str,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
        opciones: list[Opcion] | None = None,
        respuesta_correcta: bool | None = None,
    ) -> tuple[
        PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso, PreguntaEditada
    ]:
        """Delega la edición de la pregunta en el caso de uso correspondiente."""
        return await self._editar_pregunta.execute(
            pregunta_id=pregunta_id,
            texto=texto,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
        )
