import uuid

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository


class TestSQLAlchemyComisionRepositoryIntegration:
    async def test_guardar_y_obtener_con_docentes_vacio(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear("Vic", "vic.repo@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        comision = Comision.crear("Ingeniería de Software", "lu 10-12", admin.id)

        await repo.guardar(comision)
        recuperada = await repo.obtener_por_id(comision.id)

        assert recuperada is not None
        assert recuperada.materia == "Ingeniería de Software"
        assert recuperada.docentes_asignados == []

    async def test_actualizar_agrega_docente_asignado(self, session):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)

        docente = Usuario.crear("Ana", "ana3@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)
        admin = Usuario.crear("Vic", "vic.repo2@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)

        comision = Comision.crear("IS", "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        comision.asignar_docente(docente.id)
        await comision_repo.actualizar(comision)

        recuperada = await comision_repo.obtener_por_id(comision.id)
        assert recuperada.docentes_asignados == [docente.id]

    async def test_obtener_por_id_inexistente_retorna_none(self, session):
        repo = SQLAlchemyComisionRepository(session)

        assert await repo.obtener_por_id(uuid.uuid4()) is None

    async def test_actualizar_comision_inexistente_lanza_value_error(self, session):
        repo = SQLAlchemyComisionRepository(session)
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())

        with pytest.raises(ValueError):
            await repo.actualizar(comision)
