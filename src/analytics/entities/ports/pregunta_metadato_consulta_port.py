"""Puerto de consulta de metadatos de `PreguntaPlantilla`, dueña de BC Banco de Preguntas.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Analytics importe directamente ningún módulo de `src/banco_preguntas/`.
Copia propia del BC con DTO propio, mismo criterio que
`src/analytics/entities/ports/comision_consulta_port.py` (`US-4.2.2`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MetadatoPreguntaResumen:
    """Representación mínima de los metadatos de clasificación de una pregunta.

    No reexporta `MetadatosPregunta` de Banco de Preguntas — copia propia de Analytics.
    """

    unidad_tematica: str
    tema: str


class PreguntaMetadatoConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `PreguntaPlantilla` de Banco de Preguntas."""

    @abstractmethod
    async def obtener_metadatos(
        self, pregunta_ids: list[UUID]
    ) -> dict[UUID, MetadatoPreguntaResumen]:
        """Resuelve el metadato de cada `pregunta_id` encontrado, en una sola consulta por lote.

        `pregunta_ids` vacía → `dict` vacío, sin consultar la base. Un id que no corresponde a
        ninguna pregunta simplemente no aparece en el resultado — no lanza error. El metadato
        no depende del estado `activa` (una pregunta eliminada, baja lógica, también aparece).
        """
        ...
