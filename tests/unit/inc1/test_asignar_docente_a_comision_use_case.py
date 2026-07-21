import uuid

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, UsuarioNoEsDocente
from src.identidad.entities.eventos import DocenteAsignado
from src.identidad.entities.usuario import TipoPerfil, Usuario
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from tests.unit.inc1._fakes import FakeComisionRepository, FakeUsuarioRepository


class TestAsignarDocenteAComisionUseCase:
    async def test_asigna_docente_valido(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        docente = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        await comision_repo.guardar(comision)

        use_case = AsignarDocenteAComisionUseCase(comision_repo, usuario_repo)
        resultado, evento = await use_case.execute(comision.id, docente.id)

        assert docente.id in resultado.docentes_asignados
        assert isinstance(evento, DocenteAsignado)
        assert evento.comision_id == comision.id
        assert evento.docente_id == docente.id

    async def test_rechaza_usuario_que_no_es_docente(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        estudiante = Usuario.crear("Est", "est@fiuner.edu.ar", "hash", TipoPerfil.ESTUDIANTE)
        await usuario_repo.guardar(estudiante)
        comision = Comision.crear("IS", "lu 10-12", uuid.uuid4())
        await comision_repo.guardar(comision)

        use_case = AsignarDocenteAComisionUseCase(comision_repo, usuario_repo)

        with pytest.raises(UsuarioNoEsDocente):
            await use_case.execute(comision.id, estudiante.id)

        assert comision.docentes_asignados == []

    async def test_rechaza_comision_inexistente(self):
        usuario_repo = FakeUsuarioRepository()
        comision_repo = FakeComisionRepository()
        docente = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)

        use_case = AsignarDocenteAComisionUseCase(comision_repo, usuario_repo)

        with pytest.raises(ComisionNoExiste):
            await use_case.execute(uuid.uuid4(), docente.id)
