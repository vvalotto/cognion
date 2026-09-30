"""Caso de uso: edición de una pregunta existente del banco."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import PreguntaNoExiste
from src.banco_preguntas.entities.eventos import PreguntaEditada
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.use_cases.verificar_autorizacion_materia import (
    VerificarAutorizacionMateriaService,
)


class EditarPreguntaUseCase:
    """Orquesta la edición de una pregunta, delegando invariantes en su tipo concreto."""

    def __init__(
        self,
        pregunta_repositorio: PreguntaRepositoryPort,
        verificador_autorizacion: VerificarAutorizacionMateriaService,
    ) -> None:
        """Recibe el repositorio de preguntas y el servicio de autorización por materia."""
        self._pregunta_repositorio = pregunta_repositorio
        self._verificador_autorizacion = verificador_autorizacion

    async def execute(
        self,
        pregunta_id: UUID,
        metadatos: MetadatosPregunta,
        opciones: list[Opcion] | None = None,
        respuesta_correcta: bool | None = None,
        docente_id: UUID | None = None,
    ) -> tuple[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso, PreguntaEditada]:
        """Edita la pregunta según su tipo concreto y persiste los cambios.

        Levanta `PreguntaNoExiste`, `PreguntaInactiva`, `OpcionesInvalidas` (esta última
        propagada desde la entidad) o `MateriaNoAutorizada` (`docente_id` sin ninguna
        Comisión asignada en la materia del banco de la pregunta, `US-ADJ-57`).
        """
        pregunta = await self._pregunta_repositorio.obtener_por_id(pregunta_id)
        if pregunta is None:
            raise PreguntaNoExiste(pregunta_id)

        await self._verificador_autorizacion.verificar(pregunta.banco_id, docente_id)

        if isinstance(pregunta, PreguntaPlantillaOpcionMultiple):
            pregunta.editar(metadatos=metadatos, opciones=opciones or [])
        else:
            pregunta.editar(metadatos=metadatos, respuesta_correcta=bool(respuesta_correcta))

        await self._pregunta_repositorio.actualizar(pregunta)

        evento = PreguntaEditada(pregunta_id=pregunta.id, banco_id=pregunta.banco_id)
        return pregunta, evento
