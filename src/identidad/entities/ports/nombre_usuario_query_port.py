"""Puerto de consulta de nombres de usuario por lote (`US-9.4.2`, `ADR-026`).

Separado de `CuentaQueryPort` (administración de cuentas) por responsabilidad: es una consulta mínima
que consumen otros BC. Actividad Evaluativa lo usa, vía su `EstudianteConsultaPort`, para mostrar
nombres en el canal en vivo sin leer la tabla `usuario` de este BC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class NombreUsuarioQueryPort(ABC):
    """Consulta de solo lectura de `nombre` por id de `Usuario`."""

    @abstractmethod
    async def obtener_nombres(self, ids: list[UUID]) -> dict[UUID, str]:
        """Devuelve `{usuario_id: nombre}` para los ids que existen, en una sola consulta.

        Los ids sin cuenta no aparecen en el dict; una lista vacía devuelve `{}` sin consultar.
        """
        ...
