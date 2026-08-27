"""Puerto de consulta (CQRS) para `Evaluacion` no finalizadas — `VerificadorDeVencimientos`.

Separado de `EventStorePort` (append/replay por stream) porque acá la operación es una
consulta transversal a todos los streams de `Evaluacion`, no la reconstrucción de uno solo —
mismo criterio de separación command/query ya aplicado en `CuentaQueryPort` (Incremento 2) y
`BancosController` (`US-2.1.7`) para no ensanchar un puerto de escritura con responsabilidades
de lectura masiva.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion


@dataclass(frozen=True)
class EvaluacionActivaResumen:
    """Resumen de una `Evaluacion` no `Finalizada`, para las Reglas 1 y 2 del Verificador."""

    evaluacion_id: UUID
    actividad_id: UUID
    estado: EstadoEvaluacion
    ultima_actividad_en: datetime


class EvaluacionActivaQueryPort(ABC):
    """Consulta de solo lectura sobre toda `Evaluacion` que no llegó a `Finalizada` todavía."""

    @abstractmethod
    async def listar_no_finalizadas(self) -> list[EvaluacionActivaResumen]:
        """Devuelve el resumen de cada `Evaluacion` en estado `EnCurso` o `Suspendida`.

        Lista vacía si no hay ninguna. Nunca incluye una `Evaluacion` `Finalizada`.
        """
