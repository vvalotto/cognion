"""Controller de la API para la edición y la baja de preguntas.

Separado de `PreguntasController` (carga) por responsabilidad, mismo criterio que el resto del
proyecto para no pasar el umbral de CBO (`IQ-01`): al presentar, el controller único llegó a 12/10.
"""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.interface_adapters.presenters.banco_presenter import (
    PreguntaSalida,
    presentar_pregunta,
)
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase
from src.banco_preguntas.use_cases.eliminar_pregunta import EliminarPreguntaUseCase


class PreguntasEdicionController:
    """Adapta requests HTTP a los casos de uso de edición y baja de preguntas."""

    def __init__(
        self, editar_pregunta: EditarPreguntaUseCase, eliminar_pregunta: EliminarPreguntaUseCase
    ) -> None:
        """Recibe los casos de uso de edición y eliminación de pregunta."""
        self._editar_pregunta = editar_pregunta
        self._eliminar_pregunta = eliminar_pregunta

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
