"""Caso de uso: el Docente cierra la pregunta actual de la sesión en vivo (US-6.2.5, RF-09)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    PreguntaYaCerrada,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import PreguntaEnVivoCerrada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import (
    DetalleCorreccionPregunta,
    PreguntaConsultaPort,
)
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    OpcionDistribuida,
    ParticipanteEnRanking,
    ProyeccionesEnVivoQueryPort,
)
from src.actividad_evaluativa.use_cases._resolucion_nombres import resolver_nombres

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


def _payload(evento: PreguntaEnVivoCerrada) -> dict[str, Any]:
    """Arma el payload persistido de `PreguntaEnVivoCerrada` (sin ranking ni histograma)."""
    return {
        "sesion_id": str(evento.sesion_id),
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "pregunta_id": str(evento.pregunta_id),
        "ocurrido_en": evento.ocurrido_en.isoformat(),
    }


def _mensaje_cierre(
    evento: PreguntaEnVivoCerrada,
    detalle: DetalleCorreccionPregunta,
    distribucion: list[OpcionDistribuida],
    ranking: list[ParticipanteEnRanking],
) -> dict[str, Any]:
    """Arma el único mensaje de broadcast del cierre: correcta + histograma + ranking (§16)."""
    return {
        "tipo": "pregunta_cerrada",
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "respuesta_correcta": {
            "contenido": detalle.contenido_correcto,
            "texto": detalle.texto,
            "opciones": detalle.opciones,
        },
        "distribucion": [{"opcion": d.opcion, "cantidad": d.cantidad} for d in distribucion],
        "ranking": [
            {
                "posicion": r.posicion,
                "estudiante_id": str(r.estudiante_id),
                "puntaje_acumulado": r.puntaje_acumulado,
                "nombre": r.nombre,
            }
            for r in ranking
        ],
    }


class CerrarPreguntaActualUseCase:
    """Orquesta el cierre: validación, persistencia y broadcast leyendo los read models."""

    def __init__(
        self,
        event_store: EventStorePort,
        proyecciones: ProyeccionesEnVivoQueryPort,
        pregunta_consulta: PreguntaConsultaPort,
        canal: CanalTiempoRealPort,
        estudiante_consulta: EstudianteConsultaPort,
    ) -> None:
        """Recibe el event store, la lectura de proyecciones, la consulta de Banco, el canal y la
        consulta de Identidad.
        """
        self._event_store = event_store
        self._proyecciones = proyecciones
        self._pregunta_consulta = pregunta_consulta
        self._canal = canal
        self._estudiante_consulta = estudiante_consulta

    async def execute(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Cierra la pregunta actual y transmite el resultado a todos los conectados.

        Levanta `SesionNoExiste`, `SesionNoEnCurso`, `OpcionesNoMostradasTodavia` o
        `PreguntaYaCerrada` (incluida la carrera de dos cierres simultáneos, que el chequeo
        optimista del event store resuelve dejando ganar a uno). No calcula nada pesado — lee
        los read models ya acumulados (RNF de rendimiento) y publica recién después de persistir.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        sesion.cerrar_pregunta()
        evento = PreguntaEnVivoCerrada.desde_sesion(sesion, datetime.now(UTC))

        try:
            await self._event_store.append(
                AGGREGATE_TYPE_SESION,
                sesion_id,
                len(eventos),
                [EventoParaAlmacenar(event_type="PreguntaEnVivoCerrada", payload=_payload(evento))],
            )
        except ConcurrenciaOptimistaError as exc:
            raise PreguntaYaCerrada(sesion_id) from exc

        detalle = await self._pregunta_consulta.obtener_detalle_correccion(evento.pregunta_id)
        distribucion = await self._proyecciones.distribucion(sesion_id, evento.pregunta_id)
        ranking = await self._proyecciones.ranking(sesion_id)
        nombres = await resolver_nombres(
            self._estudiante_consulta, (r.estudiante_id for r in ranking)
        )
        ranking_con_nombre = [replace(r, nombre=nombres[r.estudiante_id]) for r in ranking]
        await self._canal.publicar(
            sesion_id, _mensaje_cierre(evento, detalle, distribucion, ranking_con_nombre)
        )
        return sesion
