"""Gateway SQLAlchemy que implementa `CuentaQueryPort` (RF-03)."""

from __future__ import annotations

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.cuenta_query_port import CuentaQueryPort
from src.identidad.entities.resultado_paginado_cuentas import ResultadoPaginadoCuentas
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import (
    AdministradorModel,
    DocenteModel,
    EstudianteModel,
    UsuarioModel,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil

_MODEL_POR_ROL: dict[TipoPerfil, type[AdministradorModel | DocenteModel | EstudianteModel]] = {
    TipoPerfil.ADMINISTRADOR: AdministradorModel,
    TipoPerfil.DOCENTE: DocenteModel,
    TipoPerfil.ESTUDIANTE: EstudianteModel,
}


class SQLAlchemyCuentaQueryRepository(CuentaQueryPort):
    """Consulta cuentas de usuario filtradas por rol/estado/búsqueda.

    Delega el armado de cada `Usuario` en `SQLAlchemyUsuarioRepository.obtener_por_id()` (API
    pública) en vez de duplicar la resolución de perfil.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar y arma el repositorio de usuarios interno."""
        self._session = session
        self._usuario_repo = SQLAlchemyUsuarioRepository(session)

    async def listar(
        self,
        rol: TipoPerfil | None,
        estado: str | None,
        busqueda: str | None,
        pagina: int = 1,
        tamanio_pagina: int = 20,
    ) -> ResultadoPaginadoCuentas:
        """Lista usuarios filtrados (AND) por rol, estado (`activa`/`bloqueada`) y búsqueda.

        Devuelve la página pedida, ordenada por `creado_en` (desempate por `id`), junto con
        el `total` de cuentas que matchean los filtros, sin paginar.
        """
        filtros: list[ColumnElement[bool]] = []
        joins: list[type[AdministradorModel | DocenteModel | EstudianteModel]] = []
        if rol is not None:
            model_cls = _MODEL_POR_ROL[rol]
            joins.append(model_cls)
        if estado == "activa":
            filtros.append(UsuarioModel.bloqueada.is_(False))
        elif estado == "bloqueada":
            filtros.append(UsuarioModel.bloqueada.is_(True))
        if busqueda:
            patron = f"%{busqueda}%"
            filtros.append(
                or_(UsuarioModel.nombre.ilike(patron), UsuarioModel.email.ilike(patron))
            )

        total_query = select(func.count()).select_from(UsuarioModel)
        for model_cls in joins:
            total_query = total_query.join(model_cls, model_cls.id == UsuarioModel.id)
        total_query = total_query.where(*filtros)
        total = (await self._session.execute(total_query)).scalar_one()

        query = select(UsuarioModel.id)
        for model_cls in joins:
            query = query.join(model_cls, model_cls.id == UsuarioModel.id)
        query = (
            query.where(*filtros)
            .order_by(UsuarioModel.creado_en, UsuarioModel.id)
            .limit(tamanio_pagina)
            .offset((pagina - 1) * tamanio_pagina)
        )

        resultado = await self._session.execute(query)
        usuarios: list[Usuario] = []
        for usuario_id in resultado.scalars().all():
            usuario = await self._usuario_repo.obtener_por_id(usuario_id)
            if usuario is not None:
                usuarios.append(usuario)
        return ResultadoPaginadoCuentas(cuentas=usuarios, total=total)
