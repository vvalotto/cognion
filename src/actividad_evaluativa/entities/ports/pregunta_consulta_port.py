"""Puerto de consulta de preguntas activas, dueño de BC Banco de Preguntas.

Comunicación entre BCs solo por puertos definidos en `entities/ports/` (CLAUDE.md) — este
puerto evita que Actividad Evaluativa importe directamente ningún módulo de
`src/banco_preguntas/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ContenidoPregunta:
    """Texto y opciones de una `PreguntaPlantilla`, sin exponer la respuesta correcta.

    `opciones` es `None` para Verdadero/Falso (no tiene lista de opciones) y una lista de
    textos, en el orden original de la pregunta, para Opción Múltiple — sin marcar cuál es
    correcta (INV-AE hot spot "sin feedback de corrección", `US-3.4.6`).
    """

    texto: str
    opciones: list[str] | None


@dataclass(frozen=True)
class DetalleCorreccionPregunta:
    """Texto y respuesta correcta de una `PreguntaPlantilla` — insumo de la revisión.

    `contenido_correcto` tiene el mismo shape que `Respuesta.contenido` (`Evaluacion`), para
    que el llamador pueda comparar/mostrar ambos de forma uniforme sin conocer el tipo
    concreto de la pregunta (`US-3.2.3`, RF-13). `opciones` sigue el mismo criterio que
    `ContenidoPregunta.opciones` — `None` para Verdadero/Falso, lista de textos en el orden
    original para Opción Múltiple — para que el llamador pueda resolver el texto de
    `contenido_propio`/`contenido_correcto` (`{opcion_indice: N}`) sin conocer el tipo
    concreto de la pregunta (`US-3.4.7`).
    """

    texto: str
    contenido_correcto: dict[str, Any]
    opciones: list[str] | None


class PreguntaConsultaPort(ABC):
    """Operaciones de consulta requeridas sobre `PreguntaPlantilla` de BC Banco de Preguntas."""

    @abstractmethod
    async def contar_activas_por_materia(self, materia_id: UUID) -> int:
        """Cuenta las `PreguntaPlantilla` activas del banco de la materia (INV-AE-01)."""

    @abstractmethod
    async def listar_ids_activas_por_materia(self, materia_id: UUID) -> list[UUID]:
        """Lista los ids de las `PreguntaPlantilla` activas del banco de la materia.

        Base del sampleo aleatorio (RF-12) — el Use Case hace `random.sample` sobre esta lista,
        el puerto no sabe nada de muestreo.
        """

    @abstractmethod
    async def evaluar_correccion(self, pregunta_id: UUID, contenido: dict[str, Any]) -> bool:
        """Calcula si `contenido` es la respuesta correcta de `pregunta_id` (INV-AE-10).

        Compara contra el estado vigente de la `PreguntaPlantilla` en el momento de la
        llamada — el resultado se persiste de inmediato y queda inmutable a ediciones
        posteriores de esa pregunta en el banco.
        """

    @abstractmethod
    async def obtener_detalle_correccion(self, pregunta_id: UUID) -> DetalleCorreccionPregunta:
        """Devuelve el texto y la respuesta correcta vigente de `pregunta_id` (RF-13).

        Usado por `ObtenerRevisionEvaluacion` (`US-3.2.3`) — a diferencia de
        `evaluar_correccion`, que solo informa `bool`, la revisión necesita mostrarle al
        estudiante cuál era la respuesta correcta cuando falló o no respondió. `opciones`
        permite además resolver el texto de la respuesta propia del estudiante (`US-3.4.7`).
        """

    @abstractmethod
    async def obtener_contenido(self, pregunta_id: UUID) -> ContenidoPregunta:
        """Devuelve el texto y las opciones vigentes de `pregunta_id`, sin la respuesta correcta.

        Usado por `#est-rendir` (`US-3.4.6`) para renderizar la pregunta actual — a diferencia
        de `obtener_detalle_correccion`, que sí expone qué opción es correcta y no debe
        reusarse antes de que el estudiante finalice la evaluación.
        """
