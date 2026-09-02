"""Value Objects de resultado de la query `ObtenerRevisionEvaluacion` (US-3.2.3, RF-13).

Sin comando ni evento de dominio propio (`BC-actividad-evaluativa-modelo.md` §4) — solo
estructuran lo que devuelve la lectura de una `Evaluacion` ya `Finalizada`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DetallePreguntaRevision:
    """Detalle de una `PreguntaAsignada` dentro de la revisión de una `Evaluacion`.

    `contenido_correcto` solo viene poblado si `not respondida or not es_correcta` — RF-13
    expone la respuesta correcta únicamente cuando el estudiante falló o no respondió.
    `opciones` sigue el mismo criterio que `ContenidoPregunta.opciones` — `None` para
    Verdadero/Falso, lista de textos para Opción Múltiple — para resolver el texto de
    `contenido_propio`/`contenido_correcto` sin conocer el tipo concreto (`US-3.4.7`).
    """

    pregunta_id: UUID
    orden: int
    texto: str
    respondida: bool
    contenido_propio: dict[str, Any] | None
    es_correcta: bool
    contenido_correcto: dict[str, Any] | None
    opciones: list[str] | None


@dataclass(frozen=True)
class RevisionEvaluacion:
    """Resultado completo de `ObtenerRevisionEvaluacion` — resumen + detalle por pregunta.

    Una `PreguntaAsignada` sin `Respuesta` cuenta como incorrecta en el resumen (decisión de
    diseño de `US-3.2.3` — ver spec, sección "Decisiones de diseño").
    """

    evaluacion_id: UUID
    cantidad_preguntas: int
    cantidad_correctas: int
    cantidad_incorrectas: int
    detalle: list[DetallePreguntaRevision]
