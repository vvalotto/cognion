from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import (
    Administrador,
    Docente,
    Estudiante,
    Perfil,
    TipoPerfil,
    Usuario,
)
from src.identidad.frameworks.db.models import (
    AdministradorModel,
    DocenteModel,
    EstudianteModel,
    UsuarioModel,
)

_MODEL_POR_PERFIL = {
    TipoPerfil.ADMINISTRADOR: AdministradorModel,
    TipoPerfil.DOCENTE: DocenteModel,
    TipoPerfil.ESTUDIANTE: EstudianteModel,
}

_ENTITY_POR_PERFIL = {
    TipoPerfil.ADMINISTRADOR: Administrador,
    TipoPerfil.DOCENTE: Docente,
    TipoPerfil.ESTUDIANTE: Estudiante,
}


class SQLAlchemyUsuarioRepository(UsuarioRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def existe_email(self, email: str) -> bool:
        resultado = await self._session.execute(
            select(UsuarioModel.id).where(UsuarioModel.email == email)
        )
        return resultado.scalar_one_or_none() is not None

    async def guardar(self, usuario: Usuario) -> None:
        self._session.add(
            UsuarioModel(
                id=usuario.id,
                nombre=usuario.nombre,
                email=usuario.email,
                password_hash=usuario.password_hash,
            )
        )
        # Flush intermedio: no hay `relationship()` declarada entre UsuarioModel y los
        # modelos de perfil, así que SQLAlchemy no infiere el orden de inserción a partir
        # de la FK — sin este flush, ambos inserts pueden viajar en el mismo batch y violar
        # la constraint si el perfil se ejecuta antes que el usuario.
        await self._session.flush()
        perfil_model_cls = _MODEL_POR_PERFIL[usuario.tipo_perfil]
        self._session.add(perfil_model_cls(id=usuario.id))
        await self._session.commit()

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        usuario_model = await self._session.get(UsuarioModel, usuario_id)
        if usuario_model is None:
            return None

        perfil = await self._resolver_perfil(usuario_id)
        if perfil is None:
            return None

        return Usuario(
            id=usuario_model.id,
            nombre=usuario_model.nombre,
            email=usuario_model.email,
            password_hash=usuario_model.password_hash,
            perfil=perfil,
        )

    async def _resolver_perfil(self, usuario_id: UUID) -> Perfil | None:
        for tipo_perfil, model_cls in _MODEL_POR_PERFIL.items():
            perfil_model = await self._session.get(model_cls, usuario_id)
            if perfil_model is not None:
                return _ENTITY_POR_PERFIL[tipo_perfil](id=usuario_id)
        return None
