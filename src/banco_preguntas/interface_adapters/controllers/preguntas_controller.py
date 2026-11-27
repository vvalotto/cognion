"""Controller de la API para operaciones sobre preguntas."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.interface_adapters.presenters.banco_presenter import (
    PreguntaOpcionMultipleSalida,
    PreguntaSalida,
    PreguntaVerdaderoFalsoSalida,
    presentar_pregunta,
    presentar_pregunta_opcion_multiple,
    presentar_pregunta_verdadero_falso,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase
from src.banco_preguntas.use_cases.eliminar_pregunta import EliminarPreguntaUseCase


class PreguntasController:
    """Adapta requests HTTP a los casos de uso de gestión de preguntas."""

    def __init__(
        self,
        cargar_pregunta_opcion_multiple: CargarPreguntaOpcionMultipleUseCase,
        cargar_pregunta_verdadero_falso: CargarPreguntaVerdaderoFalsoUseCase,
        editar_pregunta: EditarPreguntaUseCase,
        eliminar_pregunta: EliminarPreguntaUseCase,
    ) -> None:
        """Recibe los casos de uso de carga (uno por tipo), edición y eliminación de pregunta."""
        self._cargar_pregunta_opcion_multiple = cargar_pregunta_opcion_multiple
        self._cargar_pregunta_verdadero_falso = cargar_pregunta_verdadero_falso
        self._editar_pregunta = editar_pregunta
        self._eliminar_pregunta = eliminar_pregunta

    async def cargar_pregunta_opcion_multiple(
        self,
        banco_id: UUID,
        texto: str,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
        opciones: list[tuple[str, bool]],
        docente_id: UUID | None = None,
    ) -> PreguntaOpcionMultipleSalida:
        """Carga la pregunta de opción múltiple y la presenta; el evento se descarta acá.

        `opciones` son pares `(texto, es_correcta)`: el router no arma entidades. `docente_id`
        acota la carga a materias del Docente que llama (`US-ADJ-57`).
        """
        pregunta, _evento = await self._cargar_pregunta_opcion_multiple.execute(
            banco_id=banco_id,
            metadatos=MetadatosPregunta(texto, unidad_tematica, tema, dificultad, importancia),
            opciones=[Opcion(texto=t, es_correcta=c) for t, c in opciones],
            docente_id=docente_id,
        )
        return presentar_pregunta_opcion_multiple(pregunta)

    async def cargar_pregunta_verdadero_falso(
        self,
        banco_id: UUID,
        texto: str,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
        respuesta_correcta: bool,
        docente_id: UUID | None = None,
    ) -> PreguntaVerdaderoFalsoSalida:
        """Carga la pregunta Verdadero/Falso y la presenta; el evento se descarta acá."""
        pregunta, _evento = await self._cargar_pregunta_verdadero_falso.execute(
            banco_id=banco_id,
            metadatos=MetadatosPregunta(texto, unidad_tematica, tema, dificultad, importancia),
            respuesta_correcta=respuesta_correcta,
            docente_id=docente_id,
        )
        return presentar_pregunta_verdadero_falso(pregunta)

    async def editar_pregunta(
        self,
        pregunta_id: UUID,
        texto: str,
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
        opciones: list[tuple[str, bool]] | None = None,
        respuesta_correcta: bool | None = None,
        docente_id: UUID | None = None,
    ) -> PreguntaSalida:
        """Edita la pregunta y la presenta según su tipo; el evento se descarta acá."""
        pregunta, _evento = await self._editar_pregunta.execute(
            pregunta_id=pregunta_id,
            metadatos=MetadatosPregunta(texto, unidad_tematica, tema, dificultad, importancia),
            opciones=(
                [Opcion(texto=t, es_correcta=c) for t, c in opciones]
                if opciones is not None
                else None
            ),
            respuesta_correcta=respuesta_correcta,
            docente_id=docente_id,
        )
        return presentar_pregunta(pregunta)

    async def eliminar_pregunta(self, pregunta_id: UUID, docente_id: UUID | None = None) -> None:
        """Da de baja lógica la pregunta (INV-BP-04); el resultado no se presenta."""
        await self._eliminar_pregunta.execute(pregunta_id, docente_id=docente_id)
