"""Controller de la autorización del canal de tiempo real de una sesión en vivo (`US-12.1.1`)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.use_cases.autorizar_conexion_canal import (
    AutorizarConexionCanalUseCase,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class CanalEnVivoController:
    """Adapta el pedido de abrir el canal al caso de uso que decide si corresponde."""

    def __init__(self, autorizar: AutorizarConexionCanalUseCase) -> None:
        """Recibe el caso de uso de autorización."""
        self._autorizar = autorizar

    async def puede_conectar(self, sesion_id: UUID, usuario_id: UUID, rol: TipoPerfil) -> bool:
        """Indica si el usuario puede abrir el canal de la sesión."""
        return await self._autorizar.execute(sesion_id, usuario_id, rol)
