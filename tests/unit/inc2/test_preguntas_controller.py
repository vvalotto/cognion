import uuid

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.interface_adapters.controllers.preguntas_controller import (
    PreguntasController,
)
from src.banco_preguntas.interface_adapters.controllers.preguntas_edicion_controller import (
    PreguntasEdicionController,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase
from src.banco_preguntas.use_cases.eliminar_pregunta import EliminarPreguntaUseCase
from src.banco_preguntas.use_cases.verificar_autorizacion_materia import (
    VerificarAutorizacionMateriaService,
)
from tests.unit.inc2._fakes import (
    FakeBancoRepository,
    FakeComisionConsultaPort,
    FakePreguntaRepository,
)


def _controller(banco_repo: FakeBancoRepository, pregunta_repo: FakePreguntaRepository):
    comision_consulta = FakeComisionConsultaPort()
    return PreguntasController(
        CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo, comision_consulta),
        CargarPreguntaVerdaderoFalsoUseCase(banco_repo, pregunta_repo, comision_consulta),
    )


def _edicion_controller(banco_repo: FakeBancoRepository, pregunta_repo: FakePreguntaRepository):
    comision_consulta = FakeComisionConsultaPort()
    verificador_autorizacion = VerificarAutorizacionMateriaService(banco_repo, comision_consulta)
    return PreguntasEdicionController(
        EditarPreguntaUseCase(pregunta_repo, verificador_autorizacion),
        EliminarPreguntaUseCase(pregunta_repo, banco_repo, comision_consulta),
    )


class TestPreguntasController:
    async def test_cargar_pregunta_opcion_multiple_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)

        pregunta = await controller.cargar_pregunta_opcion_multiple(
            banco_id=banco.id,
            texto="¿Cuál es la capital de Entre Ríos?",
            unidad_tematica="Unidad 1",
            tema="Arquitectura",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
            opciones=[("Paraná", True), ("Concordia", False)],
        )

        assert pregunta.banco_id == banco.id

    async def test_cargar_pregunta_verdadero_falso_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)

        pregunta = await controller.cargar_pregunta_verdadero_falso(
            banco_id=banco.id,
            texto="El sol es una estrella.",
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
            respuesta_correcta=True,
        )

        assert pregunta.banco_id == banco.id
        assert pregunta.respuesta_correcta is True

    async def test_eliminar_pregunta_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)
        pregunta = await controller.cargar_pregunta_verdadero_falso(
            banco_id=banco.id,
            texto="El sol es una estrella.",
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
            respuesta_correcta=True,
        )

        resultado = await _edicion_controller(banco_repo, pregunta_repo).eliminar_pregunta(
            pregunta_id=pregunta.id
        )

        assert resultado is None
        baja = await pregunta_repo.obtener_por_id(pregunta.id)
        assert baja is not None
        assert baja.activa is False

    async def test_editar_pregunta_presenta_la_pregunta_segun_su_tipo(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)
        pregunta = await controller.cargar_pregunta_verdadero_falso(
            banco_id=banco.id,
            texto="El sol es una estrella.",
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
            respuesta_correcta=True,
        )

        editada = await _edicion_controller(banco_repo, pregunta_repo).editar_pregunta(
            pregunta_id=pregunta.id,
            texto="El sol es una estrella enana.",
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.BAJO,
            importancia=Importancia.ALTO,
            respuesta_correcta=False,
        )

        assert editada.texto == "El sol es una estrella enana."
        assert editada.respuesta_correcta is False
        assert editada.dificultad is Dificultad.BAJO
