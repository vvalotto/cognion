"""Gateway SQLAlchemy que implementa `CuentaQueryPort` (RF-03)."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.cuenta_query_port import CuentaQueryPort
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
        self, rol: TipoPerfil | None, estado: str | None, busqueda: str | None
    ) -> list[Usuario]:
        """Lista usuarios filtrados (AND) por rol, estado (`activa`/`bloqueada`) y búsqueda."""
        query = select(UsuarioModel.id)
        if rol is not None:
            model_cls = _MODEL_POR_ROL[rol]
            query = query.join(model_cls, model_cls.id == UsuarioModel.id)
        if estado == "activa":
            query = query.where(UsuarioModel.bloqueada.is_(False))
        elif estado == "bloqueada":
            query = query.where(UsuarioModel.bloqueada.is_(True))
        if busqueda:
            patron = f"%{busqueda}%"
            query = query.where(
                or_(UsuarioModel.nombre.ilike(patron), UsuarioModel.email.ilike(patron))
            )

        resultado = await self._session.execute(query)
        usuarios: list[Usuario] = []
        for usuario_id in resultado.scalars().all():
            usuario = await self._usuario_repo.obtener_por_id(usuario_id)
            if usuario is not None:
                usuarios.append(usuario)
        return usuarios
