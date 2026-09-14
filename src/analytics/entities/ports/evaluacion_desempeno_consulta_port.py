"""Puerto de consulta (CQRS, solo lectura) del desempeño de un estudiante en evaluaciones.

Analytics no crea su propio event store (`BC-analytics-modelo.md` §2) — este puerto es la
única forma en que el resto del BC lee el event store ajeno de Actividad Evaluativa, sin
conocer SQLAlchemy ni la tabla `events`. Consumido por `US-4.1.2` y toda la Iteración 2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class EvaluacionDesempenoResumen:
    """Resumen de una `Evaluacion` finalizada, solo con lo que Analytics necesita.

    No expone el aggregate `Evaluacion` ajeno — mismo criterio de DTO propio que
    `MateriaDTO` (`entities/ports/materia_consulta_port.py` de Actividad Evaluativa).
    """

    evaluacion_id: UUID
    actividad_id: UUID
    materia_id: UUID
    finalizada_en: datetime
    cantidad_correctas: int
    cantidad_incorrectas: int


@dataclass(frozen=True)
class ActividadResumen:
    """Metadatos mínimos de una actividad para resolver su roster aplicable (`US-ADJ-47`).

    `comisiones_ids` vacío = visible a todas las comisiones de la materia, mismo significado
    que en `ActividadEvaluativaPeriodoAbierto` (BC Actividad Evaluativa).
    """

    materia_id: UUID
    comisiones_ids: frozenset[UUID]


@dataclass(frozen=True)
class RespuestaVigente:
    """Una respuesta vigente (INV-AE-09) de una `Evaluacion` finalizada de una materia.

    `estudiante_id` viaja en la fila por fidelidad con `BC-analytics-modelo.md` §5, aunque
    `ObtenerTasaErrorPorTemaUseCase` (`US-4.2.4`) no lo necesite hoy — agrega solo por
    `pregunta_id` a nivel de materia/comisión.
    """

    pregunta_id: UUID
    estudiante_id: UUID
    es_correcta: bool


class EvaluacionDesempenoConsultaPort(ABC):
    """Consulta de solo lectura: evaluaciones finalizadas de un estudiante, con su desempeño."""

    @abstractmethod
    async def listar_evaluaciones_finalizadas(
        self, estudiante_id: UUID, materia_id: UUID | None
    ) -> list[EvaluacionDesempenoResumen]:
        """Devuelve las `Evaluacion` finalizadas del estudiante, opcionalmente filtradas.

        Sin `materia_id`, devuelve las de todas las materias. Una `Evaluacion` sin evento
        `EvaluacionFinalizada` nunca aparece en el resultado — Analytics solo reporta sobre
        evaluaciones terminadas.
        """

    @abstractmethod
    async def listar_respuestas_vigentes_de_materia(
        self, materia_id: UUID, estudiante_ids: list[UUID] | None
    ) -> list[RespuestaVigente]:
        """Devuelve las respuestas vigentes de toda `Evaluacion` finalizada de la materia.

        `estudiante_ids` acota el agregado a esos estudiantes (comisión elegida); `None` agrega
        todas las comisiones de la materia (`US-4.2.4`, RF-17). Materia sin `Evaluacion`
        finalizadas → lista vacía.
        """

    @abstractmethod
    async def listar_actividades_abiertas(self, materia_id: UUID, comision_id: UUID) -> list[UUID]:
        """Devuelve los `actividad_id` abiertos *ahora* y visibles a `comision_id` (RF-20).

        "Abierta ahora" es `fecha_apertura ≤ ahora ≤ fecha_cierre` y `cerrada_manualmente =
        False` — el estado *actual* de `ActividadEvaluativaPeriodoAbierto`, que puede haber
        cambiado por `PeriodoDisponibilidadModificado`/`ActividadEvaluativaCerrada` desde la
        creación. "Visible" es `comisiones_ids` vacío (todas las comisiones de la materia) o
        `comision_id ∈ comisiones_ids`. Insumo de "actividades pendientes" en
        `ObtenerDesempenoPorComisionUseCase` (`US-ADJ-44`).
        """

    @abstractmethod
    async def obtener_titulos_actividades(self, actividad_ids: list[UUID]) -> dict[UUID, str]:
        """Resuelve el `titulo` *actual* de cada `actividad_id` (RF-21).

        `titulo` puede haber cambiado por `TituloActividadModificado` desde la creación — se
        reconstruye el stream completo, mismo criterio que `listar_actividades_abiertas`
        (`US-ADJ-44`). `actividad_ids` vacía devuelve `dict` vacío, sin consultar la base. Un
        id que no corresponde a ninguna actividad simplemente no aparece en el resultado.
        """

    @abstractmethod
    async def obtener_actividad_resumen(self, actividad_id: UUID) -> ActividadResumen | None:
        """Resuelve `materia_id`/`comisiones_ids` de una actividad, o `None` si no existe (RF-23).

        Insumo para resolver el roster aplicable de `ObtenerCompletitudPorActividadUseCase`
        (`US-ADJ-47`) — reusa el mismo cruce hacia `ActividadEvaluativaPeriodoAbierto` que
        `listar_actividades_abiertas` (`US-ADJ-44`).
        """

    @abstractmethod
    async def listar_estados_de_actividad(
        self, actividad_id: UUID, estudiante_ids: list[UUID]
    ) -> dict[UUID, str]:
        """Estado (`"en_curso"`, `"suspendida"` o `"finalizada"`) de la `Evaluacion` de cada
        estudiante de `estudiante_ids` para `actividad_id` (RF-23).

        Un `estudiante_id` ausente del dict nunca inició esa actividad — "sin_iniciar" es
        responsabilidad del Use Case, no de este puerto.
        """
