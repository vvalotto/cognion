"""Caso de uso: alta de una `ActividadEvaluativaEnVivo` (US-6.1.2, RF-08)."""

from __future__ import annotations

import random
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import ComisionNoExiste, PreguntasInsuficientes
from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoCreada
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE = "ActividadEvaluativaEnVivo"


class CrearSesionEnVivoUseCase:
    """Orquesta la creación de la sesión y su persistencia en el event store del BC."""

    def __init__(
        self,
        comision_consulta: ComisionConsultaPort,
        pregunta_consulta: PreguntaConsultaPort,
        event_store: EventStorePort,
    ) -> None:
        """Recibe los puertos de consulta a Identidad/Banco de Preguntas y el event store."""
        self._comision_consulta = comision_consulta
        self._pregunta_consulta = pregunta_consulta
        self._event_store = event_store

    async def execute(
        self,
        comision_id: UUID,
        cantidad_preguntas: int,
        tiempo_limite_por_pregunta_segundos: int,
        unidad_tematica: str | None = None,
        tema: str | None = None,
    ) -> ActividadEvaluativaEnVivo:
        """Crea la sesión validando INV-AEV-01/02 y la persiste como primer evento del stream.

        Levanta `ComisionNoExiste` si `comision_id` no corresponde a ninguna Comisión,
        `PreguntasInsuficientes` si `cantidad_preguntas` excede las preguntas activas del banco
        de la materia de esa Comisión (filtradas por `unidad_tematica`/`tema` si se eligieron,
        combinados con AND). `TiempoLimiteInvalido` se valida en el aggregate (INV-AEV-02).

        El set de preguntas se sampleá y fija acá, al crear (no al iniciar la sesión) — todos
        los estudiantes que se unan reciben el mismo set (RF-08).
        """
        materia_id = await self._comision_consulta.obtener_materia_id(comision_id)
        if materia_id is None:
            raise ComisionNoExiste(comision_id)

        ids_disponibles = await self._pregunta_consulta.listar_ids_activas_por_materia(
            materia_id, unidad_tematica, tema
        )
        if cantidad_preguntas > len(ids_disponibles):
            raise PreguntasInsuficientes(cantidad_preguntas, len(ids_disponibles))

        muestra = random.sample(ids_disponibles, k=cantidad_preguntas)
        sesion = ActividadEvaluativaEnVivo.crear(
            comision_id=comision_id,
            materia_id=materia_id,
            preguntas=Evaluacion.armar_preguntas_asignadas(muestra),
            tiempo_limite_por_pregunta_segundos=tiempo_limite_por_pregunta_segundos,
            unidad_tematica=unidad_tematica,
            tema=tema,
        )

        evento = SesionEnVivoCreada.desde_sesion(sesion)
        payload = {
            "sesion_id": str(evento.sesion_id),
            "comision_id": str(evento.comision_id),
            "materia_id": str(evento.materia_id),
            "preguntas": [
                {"pregunta_id": str(p.pregunta_id), "orden": p.orden} for p in evento.preguntas
            ],
            "tiempo_limite_por_pregunta_segundos": evento.tiempo_limite_por_pregunta_segundos,
            "unidad_tematica": evento.unidad_tematica,
            "tema": evento.tema,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE,
            sesion.id,
            0,
            [EventoParaAlmacenar(event_type="SesionEnVivoCreada", payload=payload)],
        )

        return sesion
