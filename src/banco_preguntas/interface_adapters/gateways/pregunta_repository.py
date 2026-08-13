"""Gateway SQLAlchemy que implementa `PreguntaRepositoryPort`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
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

    async def obtener_por_id(
        self, pregunta_id: UUID
    ) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso | None:
        """Busca una pregunta por id; devuelve `None` si no existe."""
        modelo = await self._session.get(PreguntaPlantillaModel, pregunta_id)
        if modelo is None:
            return None
        return self._a_entidad(modelo)

    async def filtrar(
        self,
        banco_id: UUID,
        unidad: str | None = None,
        tema: str | None = None,
        dificultad: str | None = None,
        importancia: str | None = None,
    ) -> list[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso]:
        """Lista las preguntas activas del banco que matchean todos los filtros provistos."""
        query = select(PreguntaPlantillaModel).where(
            PreguntaPlantillaModel.banco_id == banco_id,
            PreguntaPlantillaModel.activa.is_(True),
        )
        if unidad is not None:
            query = query.where(PreguntaPlantillaModel.unidad_tematica == unidad)
        if tema is not None:
            query = query.where(PreguntaPlantillaModel.tema == tema)
        if dificultad is not None:
            query = query.where(PreguntaPlantillaModel.dificultad == dificultad)
        if importancia is not None:
            query = query.where(PreguntaPlantillaModel.importancia == importancia)

        resultado = await self._session.execute(query)
        return [self._a_entidad(modelo) for modelo in resultado.scalars().all()]

    @staticmethod
    def _a_entidad(
        modelo: PreguntaPlantillaModel,
    ) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso:
        """Mapea una fila de `pregunta_plantilla` al aggregate concreto según su `tipo`."""
        if modelo.tipo == TIPO_VERDADERO_FALSO:
            return PreguntaPlantillaVerdaderoFalso(
                id=modelo.id,
                banco_id=modelo.banco_id,
                texto=modelo.texto,
                respuesta_correcta=bool(modelo.respuesta_correcta),
                unidad_tematica=modelo.unidad_tematica,
                tema=modelo.tema,
                dificultad=Dificultad(modelo.dificultad),
                importancia=Importancia(modelo.importancia),
                activa=modelo.activa,
            )

        return PreguntaPlantillaOpcionMultiple(
            id=modelo.id,
            banco_id=modelo.banco_id,
            texto=modelo.texto,
            opciones=[
                Opcion(texto=o["texto"], es_correcta=o["es_correcta"])
                for o in (modelo.opciones or [])
            ],
            unidad_tematica=modelo.unidad_tematica,
            tema=modelo.tema,
            dificultad=Dificultad(modelo.dificultad),
            importancia=Importancia(modelo.importancia),
            activa=modelo.activa,
        )

    async def actualizar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Guarda los cambios de una pregunta ya existente (actualización, no alta)."""
        modelo = await self._session.get(PreguntaPlantillaModel, pregunta.id)
        assert modelo is not None

        modelo.texto = pregunta.texto
        modelo.unidad_tematica = pregunta.unidad_tematica
        modelo.tema = pregunta.tema
        modelo.dificultad = pregunta.dificultad.value
        modelo.importancia = pregunta.importancia.value
        modelo.activa = pregunta.activa

        if isinstance(pregunta, PreguntaPlantillaVerdaderoFalso):
            modelo.respuesta_correcta = pregunta.respuesta_correcta
        else:
            modelo.opciones = [
                {"texto": opcion.texto, "es_correcta": opcion.es_correcta}
                for opcion in pregunta.opciones
            ]

        await self._session.commit()
