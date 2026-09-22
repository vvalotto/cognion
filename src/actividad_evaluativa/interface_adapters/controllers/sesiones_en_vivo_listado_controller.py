"""Controller de la API para listar las sesiones en vivo de una Comisión (US-6.3.2).

Separado de `SesionesEnVivoQueryController` — sumar `ListarSesionesEnVivoUseCase` ahí hacía
saltar `CBOAnalyzer` a 11/10 (CRITICAL) en el pre-push, mismo patrón de CRITICAL de CBO ya visto
en `BancosController`/`US-2.1.7` y documentado como riesgo en la spec de esta US.
"""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import (
    SesionEnVivoResumen,
)
from src.actividad_evaluativa.use_cases.listar_sesiones_en_vivo import ListarSesionesEnVivoUseCase
from src.shared.entities.tipo_perfil import TipoPerfil


class SesionesEnVivoListadoController:
    """Adapta el request HTTP de listado al caso de uso de sesiones en vivo por Comisión."""

    def __init__(self, listar_sesiones: ListarSesionesEnVivoUseCase) -> None:
        """Recibe el caso de uso de listado de sesiones."""
        self._listar_sesiones = listar_sesiones

    async def listar_sesiones(
        self,
        usuario_id: UUID,
        rol: TipoPerfil,
        comision_id: UUID | None,
        estados: list[EstadoSesionEnVivo],
    ) -> list[SesionEnVivoResumen]:
        """Devuelve las sesiones en vivo visibles para `usuario_id` según su rol."""
        return await self._listar_sesiones.execute(usuario_id, rol, comision_id, estados)
