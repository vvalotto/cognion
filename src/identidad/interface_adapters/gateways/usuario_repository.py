"""Gateway SQLAlchemy que implementa `UsuarioRepositoryPort`."""

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

_MODEL_POR_PERFIL: dict[TipoPerfil, type[AdministradorModel | DocenteModel | EstudianteModel]] = {
    TipoPerfil.ADMINISTRADOR: AdministradorModel,
    TipoPerfil.DOCENTE: DocenteModel,
    TipoPerfil.ESTUDIANTE: EstudianteModel,
}

# Estudiante queda fuera: su constructor exige `comision_id`, que este dict no tiene forma de
# proveer — el caso Estudiante se resuelve aparte en `_resolver_perfil` (ver isinstance abajo).
_ENTITY_POR_PERFIL: dict[TipoPerfil, type[Administrador | Docente]] = {
    TipoPerfil.ADMINISTRADOR: Administrador,
    TipoPerfil.DOCENTE: Docente,
}


class SQLAlchemyUsuarioRepository(UsuarioRepositoryPort):
    """Persiste y recupera usuarios usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las operaciones."""
        self._session = session

    async def existe_email(self, email: str) -> bool:
        """Indica si ya hay un usuario registrado con ese email."""
        resultado = await self._session.execute(
            select(UsuarioModel.id).where(UsuarioModel.email == email)
        )
        return resultado.scalar_one_or_none() is not None

    async def guardar(self, usuario: Usuario) -> None:
        """Guarda el usuario y su modelo de perfil correspondiente."""
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
        self._session.add(self._perfil_model(usuario))
        await self._session.commit()

    @staticmethod
    def _perfil_model(usuario: Usuario) -> AdministradorModel | DocenteModel | EstudianteModel:
        """Construye el modelo de perfil correspondiente al usuario."""
        if isinstance(usuario.perfil, Estudiante):
            return EstudianteModel(id=usuario.id, comision_id=usuario.perfil.comision_id)
        return _MODEL_POR_PERFIL[usuario.tipo_perfil](id=usuario.id)

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        """Busca un usuario por id junto con su perfil, o `None` si no existe."""
        usuario_model = await self._session.get(UsuarioModel, usuario_id)
        if usuario_model is None:
            return None
        return await self._armar_usuario(usuario_model)

    async def obtener_por_email(self, email: str) -> Usuario | None:
        """Busca un usuario por email junto con su perfil, o `None` si no existe."""
        resultado = await self._session.execute(
            select(UsuarioModel).where(UsuarioModel.email == email)
        )
        usuario_model = resultado.scalar_one_or_none()
        if usuario_model is None:
            return None
        return await self._armar_usuario(usuario_model)

    async def _armar_usuario(self, usuario_model: UsuarioModel) -> Usuario | None:
        """Resuelve el perfil del modelo y arma la entidad `Usuario`, o `None` si no hay perfil."""
        perfil = await self._resolver_perfil(usuario_model.id)
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
        """Busca en qué tabla de perfil está el usuario y arma la entidad correspondiente."""
        for tipo_perfil, model_cls in _MODEL_POR_PERFIL.items():
            perfil_model = await self._session.get(model_cls, usuario_id)
            if perfil_model is None:
                continue
            if isinstance(perfil_model, EstudianteModel):
                return Estudiante(id=usuario_id, comision_id=perfil_model.comision_id)
            return _ENTITY_POR_PERFIL[tipo_perfil](id=usuario_id)
        return None
