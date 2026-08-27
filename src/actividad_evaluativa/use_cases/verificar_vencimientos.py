"""Caso de uso: Policy `VerificadorDeVencimientos`, Reglas 1 y 2 (US-3.2.4).

No es un aggregate ni tiene comando/evento propio (`BC-actividad-evaluativa-modelo.md` §6b) —
reutiliza `SuspenderEvaluacionUseCase`/`FinalizarEvaluacionUseCase` con `actor="sistema"` sobre
cada `Evaluacion` que `EvaluacionActivaQueryPort` reporta como no finalizada.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaQueryPort,
    EvaluacionActivaResumen,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import FinalizarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase

AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


@dataclass(frozen=True)
class ResumenVerificacion:
    """Cantidad de `Evaluacion` afectadas por cada regla en una corrida de la Policy."""

    suspendidas: int
    finalizadas: int


class VerificarVencimientosUseCase:
    """Orquesta las Reglas 1 (inactividad) y 2 (vencimiento de período) del Verificador."""

    def __init__(
        self,
        evaluacion_activa_query: EvaluacionActivaQueryPort,
        event_store: EventStorePort,
        suspender_evaluacion: SuspenderEvaluacionUseCase,
        finalizar_evaluacion: FinalizarEvaluacionUseCase,
        umbral_inactividad: timedelta,
    ) -> None:
        """Recibe el read model, el event store (para `fecha_cierre`) y los Use Case."""
        self._evaluacion_activa_query = evaluacion_activa_query
        self._event_store = event_store
        self._suspender_evaluacion = suspender_evaluacion
        self._finalizar_evaluacion = finalizar_evaluacion
        self._umbral_inactividad = umbral_inactividad

    async def execute(self) -> ResumenVerificacion:
        """Corre las Reglas 1 y 2 sobre toda `Evaluacion` no `Finalizada` en esta pasada.

        Idempotente: una `Evaluacion` que ya cambió de estado por otra vía (otra corrida, o
        acción manual del Estudiante) no produce un segundo evento — los Use Case reutilizados
        lo capturan como no-op cuando `actor="sistema"` (INV-AE-11/12).
        """
        resumen = await self._evaluacion_activa_query.listar_no_finalizadas()
        ahora = datetime.now(UTC)
        cache_fecha_cierre: dict[UUID, datetime] = {}

        suspendidas = await self._aplicar_regla_inactividad(resumen, ahora)
        finalizadas = await self._aplicar_regla_vencimiento(resumen, ahora, cache_fecha_cierre)
        return ResumenVerificacion(suspendidas=suspendidas, finalizadas=finalizadas)

    async def _aplicar_regla_inactividad(
        self, resumen: list[EvaluacionActivaResumen], ahora: datetime
    ) -> int:
        """Regla 1: suspende toda `Evaluacion` `EnCurso` inactiva por más del umbral configurado."""
        contador = 0
        for item in resumen:
            if item.estado is not EstadoEvaluacion.EN_CURSO:
                continue
            if ahora - item.ultima_actividad_en <= self._umbral_inactividad:
                continue
            resultado = await self._suspender_evaluacion.execute(
                item.evaluacion_id, actor="sistema"
            )
            if resultado is not None:
                contador += 1
        return contador

    async def _aplicar_regla_vencimiento(
        self,
        resumen: list[EvaluacionActivaResumen],
        ahora: datetime,
        cache_fecha_cierre: dict[UUID, datetime],
    ) -> int:
        """Regla 2: finaliza toda `Evaluacion` `EnCurso`/`Suspendida` de una actividad vencida."""
        contador = 0
        for item in resumen:
            fecha_cierre = await self._fecha_cierre_de(item.actividad_id, cache_fecha_cierre)
            if fecha_cierre >= ahora:
                continue
            resultado = await self._finalizar_evaluacion.execute(
                item.evaluacion_id, actor="sistema"
            )
            if resultado is not None:
                contador += 1
        return contador

    async def _fecha_cierre_de(
        self, actividad_id: UUID, cache_fecha_cierre: dict[UUID, datetime]
    ) -> datetime:
        """Lee `fecha_cierre` del stream de la actividad, cacheado por corrida.

        `ModificarPeriodoDisponibilidad`/`CerrarActividad` (`US-3.3.1`/`US-3.3.2`, Iteración 3)
        todavía no existen — el stream de cada actividad tiene un único evento
        (`ActividadEvaluativaCreada`) hasta que esas US lo extiendan, así que alcanza con leer
        el primero.
        """
        if actividad_id in cache_fecha_cierre:
            return cache_fecha_cierre[actividad_id]
        eventos = await self._event_store.load(AGGREGATE_TYPE_ACTIVIDAD, actividad_id)
        fecha_cierre = datetime.fromisoformat(eventos[0].payload["fecha_cierre"])
        cache_fecha_cierre[actividad_id] = fecha_cierre
        return fecha_cierre
