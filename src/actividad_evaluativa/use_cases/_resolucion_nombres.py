"""Resolución compartida de nombres de Estudiantes en la sesión en vivo (`US-6.3.1`).

Usado por los use cases que arman broadcasts o respuestas HTTP con participantes/ranking —
evita repetir la lógica de "una sola consulta por lote + texto de reemplazo" en cada uno.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)

NOMBRE_SIN_RESOLVER = "Estudiante sin nombre"


async def resolver_nombres(
    consulta: EstudianteConsultaPort, ids: Iterable[UUID]
) -> dict[UUID, str]:
    """Devuelve `{estudiante_id: nombre}` para todos los `ids`, sin ids repetidos.

    Un id sin cuenta resoluble (dato inconsistente) recibe `NOMBRE_SIN_RESOLVER` en vez de
    faltar del dict — quien llama nunca necesita chequear ausencia (`US-6.3.1`).
    """
    ids_unicos = list(dict.fromkeys(ids))
    if not ids_unicos:
        return {}
    resueltos = await consulta.obtener_nombres(ids_unicos)
    return {
        estudiante_id: resueltos.get(estudiante_id, NOMBRE_SIN_RESOLVER)
        for estudiante_id in ids_unicos
    }
