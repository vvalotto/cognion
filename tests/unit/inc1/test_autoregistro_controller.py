from uuid import uuid4

from src.identidad.entities.comision import Comision
from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.interface_adapters.controllers.autoregistro_controller import (
    AutoregistroController,
)
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase
from src.identidad.use_cases.autoregistrar_estudiante import AutoregistrarEstudianteUseCase
from tests.unit.inc1._fakes import (
    FakeComisionQueryRepository,
    FakeComisionRepository,
    FakeMateriaPort,
    FakePasswordHasher,
    FakeUsuarioRepository,
)


def _controller(
    usuario_repo=None,
    hasher=None,
    comision_repo=None,
    materia_port=None,
    comision_query=None,
) -> AutoregistroController:
    usuario_repo = usuario_repo or FakeUsuarioRepository()
    hasher = hasher or FakePasswordHasher()
    comision_repo = comision_repo or FakeComisionRepository()
    materia_port = materia_port or FakeMateriaPort()
    comision_query = comision_query or FakeComisionQueryRepository()
    return AutoregistroController(
        AutoregistrarDocenteUseCase(usuario_repo, hasher),
        AutoregistrarEstudianteUseCase(usuario_repo, hasher, comision_repo),
        materia_port,
        comision_query,
    )


class TestAutoregistroController:
    async def test_autoregistrar_docente_delega_al_use_case(self):
        controller = _controller()

        usuario, evento = await controller.autoregistrar_docente(
            "Nico", "nico@fiuner.edu.ar", "Password#123x"
        )

        assert usuario.email == "nico@fiuner.edu.ar"
        assert isinstance(evento, UsuarioAutoregistrado)

    async def test_autoregistrar_estudiante_delega_al_use_case(self):
        comision_repo = FakeComisionRepository()
        comision = Comision.crear(
            materia_id=uuid4(), horario="Lunes 10-12", administrador_id=uuid4()
        )
        await comision_repo.guardar(comision)
        controller = _controller(comision_repo=comision_repo)

        usuario, evento = await controller.autoregistrar_estudiante(
            "Vale", "vale@fiuner.edu.ar", "Password#123x", comision.id
        )

        assert usuario.email == "vale@fiuner.edu.ar"
        assert isinstance(evento, UsuarioAutoregistrado)


class TestAutoregistroControllerListarMaterias:
    """Tests del selector de la pantalla de autoregistro de Estudiante (`US-ADJ-43`)."""

    async def test_listar_materias_delega_en_materia_port(self):
        materia_port = FakeMateriaPort()
        materia_id = uuid4()
        materia_port.agregar(materia_id, "Ingeniería de Software")
        controller = _controller(materia_port=materia_port)

        materias = await controller.listar_materias()

        assert len(materias) == 1
        assert materias[0].id == materia_id
        assert materias[0].nombre == "Ingeniería de Software"

    async def test_listar_materias_sin_materias_devuelve_lista_vacia(self):
        controller = _controller()

        materias = await controller.listar_materias()

        assert materias == []


class TestAutoregistroControllerListarComisionesPorMateria:
    """Tests del selector de Comisión en cascada (`US-ADJ-43`)."""

    async def test_listar_comisiones_delega_en_comision_query_port(self):
        materia_id = uuid4()
        comision = Comision.crear(
            materia_id=materia_id, horario="Lunes 10-12", administrador_id=uuid4()
        )
        comision_query = FakeComisionQueryRepository()
        comision_query.agregar_comision(comision)
        controller = _controller(comision_query=comision_query)

        comisiones = await controller.listar_comisiones_por_materia(materia_id)

        assert len(comisiones) == 1
        assert comisiones[0].id == comision.id
        assert comisiones[0].horario == "Lunes 10-12"

    async def test_listar_comisiones_de_materia_sin_comisiones_devuelve_lista_vacia(self):
        controller = _controller()

        comisiones = await controller.listar_comisiones_por_materia(uuid4())

        assert comisiones == []
