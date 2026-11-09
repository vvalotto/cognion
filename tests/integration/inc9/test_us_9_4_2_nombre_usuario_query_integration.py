"""`SQLAlchemyNombreUsuarioQueryRepository.obtener_nombres` contra PostgreSQL (US-9.4.2)."""

from __future__ import annotations

import uuid

from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.nombre_usuario_query_repository import (
    SQLAlchemyNombreUsuarioQueryRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class TestObtenerNombres:
    async def test_lista_vacia(self, session):
        assert await SQLAlchemyNombreUsuarioQueryRepository(session).obtener_nombres([]) == {}

    async def test_devuelve_nombres_de_cualquier_rol_y_omite_inexistentes(self, session):
        usuarios = SQLAlchemyUsuarioRepository(session)
        docente = Usuario.crear("Doc", "doc.942@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        admin = Usuario.crear("Adm", "adm.942@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuarios.guardar(docente)
        await usuarios.guardar(admin)

        resultado = await SQLAlchemyNombreUsuarioQueryRepository(session).obtener_nombres(
            [docente.id, admin.id, uuid.uuid4()]
        )

        assert resultado == {docente.id: "Doc", admin.id: "Adm"}
