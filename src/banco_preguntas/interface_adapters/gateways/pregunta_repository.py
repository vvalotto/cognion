"""Gateway SQLAlchemy que implementa `PreguntaRepositoryPort`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.entities.resultado_paginado_preguntas import (
    ResultadoPaginadoPreguntas,
)
from src.banco_preguntas.frameworks.db.models import PreguntaPlantillaModel

TIPO_OPCION_MULTIPLE = "opcion_multiple"
TIPO_VERDADERO_FALSO = "verdadero_falso"

# Los 4 mapeadores siguientes son funciones de módulo (no métodos) a propósito: su CC no
# computa en el WMC de SQLAlchemyPreguntaRepository, y quedan cortos por tipo concreto en vez
# de un único método con isinstance/tipo interno (US-ADJ-18).


def _modelo_desde_verdadero_falso(
    pregunta: PreguntaPlantillaVerdaderoFalso,
) -> PreguntaPlantillaModel:
    """Mapea una `PreguntaPlantillaVerdaderoFalso` al modelo SQLAlchemy."""
    return PreguntaPlantillaModel(
        id=pregunta.id,
        banco_id=pregunta.banco_id,
        tipo=TIPO_VERDADERO_FALSO,
        texto=pregunta.texto,
        opciones=None,
        respuesta_correcta=pregunta.respuesta_correcta,
        unidad_tematica=pregunta.unidad_tematica,
        tema=pregunta.tema,
        dificultad=pregunta.dificultad_valor,
        importancia=pregunta.importancia_valor,
        activa=pregunta.activa,
        fecha_creacion=pregunta.fecha_creacion,
    )


def _modelo_desde_opcion_multiple(
    pregunta: PreguntaPlantillaOpcionMultiple,
) -> PreguntaPlantillaModel:
    """Mapea una `PreguntaPlantillaOpcionMultiple` al modelo SQLAlchemy."""
    opciones = [{"texto": o.texto, "es_correcta": o.es_correcta} for o in pregunta.opciones]
    return PreguntaPlantillaModel(
        id=pregunta.id,
        banco_id=pregunta.banco_id,
        tipo=TIPO_OPCION_MULTIPLE,
        texto=pregunta.texto,
        opciones=opciones,
        respuesta_correcta=None,
        unidad_tematica=pregunta.unidad_tematica,
        tema=pregunta.tema,
        dificultad=pregunta.dificultad_valor,
        importancia=pregunta.importancia_valor,
        activa=pregunta.activa,
        fecha_creacion=pregunta.fecha_creacion,
    )


def _entidad_desde_modelo_verdadero_falso(
    modelo: PreguntaPlantillaModel, metadatos: MetadatosPregunta
) -> PreguntaPlantillaVerdaderoFalso:
    """Mapea el modelo SQLAlchemy a `PreguntaPlantillaVerdaderoFalso` — ver nota de módulo."""
    return PreguntaPlantillaVerdaderoFalso(
        id=modelo.id,
        banco_id=modelo.banco_id,
        metadatos=metadatos,
        respuesta_correcta=bool(modelo.respuesta_correcta),
        activa=modelo.activa,
        fecha_creacion=modelo.fecha_creacion,
    )


def _entidad_desde_modelo_opcion_multiple(
    modelo: PreguntaPlantillaModel, metadatos: MetadatosPregunta
) -> PreguntaPlantillaOpcionMultiple:
    """Mapea el modelo SQLAlchemy a `PreguntaPlantillaOpcionMultiple` — ver nota de módulo."""
    return PreguntaPlantillaOpcionMultiple(
        id=modelo.id,
        banco_id=modelo.banco_id,
        metadatos=metadatos,
        opciones=[
            Opcion(texto=o["texto"], es_correcta=o["es_correcta"]) for o in (modelo.opciones or [])
        ],
        activa=modelo.activa,
        fecha_creacion=modelo.fecha_creacion,
    )


def _a_entidad(
    modelo: PreguntaPlantillaModel,
) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso:
    """Mapea una fila de `pregunta_plantilla` al aggregate concreto según su `tipo`."""
    metadatos = MetadatosPregunta.desde_valores_persistidos(
        texto=modelo.texto,
        unidad_tematica=modelo.unidad_tematica,
        tema=modelo.tema,
        dificultad=modelo.dificultad,
        importancia=modelo.importancia,
    )
    if modelo.tipo == TIPO_VERDADERO_FALSO:
        return _entidad_desde_modelo_verdadero_falso(modelo, metadatos)
    return _entidad_desde_modelo_opcion_multiple(modelo, metadatos)


def _aplicar_pregunta_a_modelo(
    modelo: PreguntaPlantillaModel,
    pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso,
) -> None:
    """Copia los campos de `pregunta` al `modelo` ya persistido (mutación in-place)."""
    modelo.texto = pregunta.texto
    modelo.unidad_tematica = pregunta.unidad_tematica
    modelo.tema = pregunta.tema
    modelo.dificultad = pregunta.dificultad_valor
    modelo.importancia = pregunta.importancia_valor
    modelo.activa = pregunta.activa
    if isinstance(pregunta, PreguntaPlantillaVerdaderoFalso):
        modelo.respuesta_correcta = pregunta.respuesta_correcta
    else:
        modelo.opciones = [
            {"texto": opcion.texto, "es_correcta": opcion.es_correcta}
            for opcion in pregunta.opciones
        ]


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
            modelo = _modelo_desde_verdadero_falso(pregunta)
        else:
            modelo = _modelo_desde_opcion_multiple(pregunta)

        self._session.add(modelo)
        await self._session.commit()

    async def obtener_por_id(
        self, pregunta_id: UUID
    ) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso | None:
        """Busca una pregunta por id; devuelve `None` si no existe."""
        modelo = await self._session.get(PreguntaPlantillaModel, pregunta_id)
        if modelo is None:
            return None
        return _a_entidad(modelo)

    async def filtrar(
        self,
        banco_id: UUID,
        unidad: str | None = None,
        tema: str | None = None,
        dificultad: str | None = None,
        importancia: str | None = None,
        pagina: int | None = None,
        tamanio_pagina: int | None = None,
    ) -> ResultadoPaginadoPreguntas:
        """Lista las preguntas activas del banco que matchean todos los filtros provistos.

        `pagina`/`tamanio_pagina` son opt-in — si alguno falta, devuelve todas las preguntas
        que matchean (ver `PreguntaRepositoryPort.filtrar`).
        """
        filtros = [
            PreguntaPlantillaModel.banco_id == banco_id,
            PreguntaPlantillaModel.activa.is_(True),
        ]
        if unidad is not None:
            filtros.append(PreguntaPlantillaModel.unidad_tematica == unidad)
        if tema is not None:
            filtros.append(PreguntaPlantillaModel.tema == tema)
        if dificultad is not None:
            filtros.append(PreguntaPlantillaModel.dificultad == dificultad)
        if importancia is not None:
            filtros.append(PreguntaPlantillaModel.importancia == importancia)

        total_query = select(func.count()).select_from(PreguntaPlantillaModel).where(*filtros)
        total = (await self._session.execute(total_query)).scalar_one()

        query = (
            select(PreguntaPlantillaModel)
            .where(*filtros)
            .order_by(PreguntaPlantillaModel.fecha_creacion, PreguntaPlantillaModel.id)
        )
        if pagina is not None and tamanio_pagina is not None:
            query = query.limit(tamanio_pagina).offset((pagina - 1) * tamanio_pagina)

        resultado = await self._session.execute(query)
        preguntas = [_a_entidad(modelo) for modelo in resultado.scalars().all()]
        return ResultadoPaginadoPreguntas(preguntas=preguntas, total=total)

    async def actualizar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Guarda los cambios de una pregunta ya existente (actualización, no alta)."""
        modelo = await self._session.get(PreguntaPlantillaModel, pregunta.id)
        assert modelo is not None

        _aplicar_pregunta_a_modelo(modelo, pregunta)

        await self._session.commit()
