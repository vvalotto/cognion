"""Puerto de consultas administrativas sobre cuentas.

Implementado en interface_adapters/frameworks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.identidad.entities.resultado_paginado_cuentas import ResultadoPaginadoCuentas
from src.shared.entities.tipo_perfil import TipoPerfil


class CuentaQueryPort(ABC):
    """Consultas de solo lectura sobre cuentas de usuario para administración (RF-03).

    Separado de `UsuarioRepositoryPort` (altas/persistencia) por responsabilidad
    command/query, mismo criterio que separa `CuentasController` de `UsuariosController`.
    """

    @abstractmethod
    async def listar(
        self,
        rol: TipoPerfil | None,
        estado: str | None,
        busqueda: str | None,
        pagina: int = 1,
        tamanio_pagina: int = 20,
    ) -> ResultadoPaginadoCuentas:
        """Lista usuarios filtrados (AND) por rol, estado (`activa`/`bloqueada`) y búsqueda.

        Devuelve la página pedida (orden estable por `creado_en`) y el `total` de cuentas
        que matchean los filtros, sin paginar (`US-ADJ-05`).
        """
        ...
