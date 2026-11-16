"""Caso de uso: decide si un usuario puede abrir el canal en vivo de una sesión (US-12.1.1)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import ComisionNoAutorizada, SesionNoExiste
from src.actividad_evaluativa.use_cases.autorizar_acceso_sesion_en_vivo import (
    AutorizarAccesoSesionEnVivoUseCase,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class AutorizarConexionCanalUseCase:
    """Autoriza la conexión al canal con la regla de pertenencia a la comisión de la sesión."""

    def __init__(self, autorizar_acceso: AutorizarAccesoSesionEnVivoUseCase) -> None:
        """Recibe el caso de uso que contiene la regla (`US-12.1.2`)."""
        self._autorizar_acceso = autorizar_acceso

    async def execute(self, sesion_id: UUID, usuario_id: UUID, rol: TipoPerfil) -> bool:
        """Devuelve `True` si el usuario pertenece a la comisión de la sesión.

        Una sesión inexistente devuelve `False`, igual que un usuario sin pertenencia: quien
        llama no distingue "no existe" de "no autorizado".
        """
        try:
            await self._autorizar_acceso.execute(sesion_id, usuario_id, rol)
        except (SesionNoExiste, ComisionNoAutorizada):
            return False
        return True
