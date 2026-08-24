import uuid

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.interface_adapters.controllers.preguntas_controller import (
    PreguntasController,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase
from src.banco_preguntas.use_cases.eliminar_pregunta import EliminarPreguntaUseCase
from tests.unit.inc2._fakes import FakeBancoRepository, FakePreguntaRepository


def _controller(banco_repo: FakeBancoRepository, pregunta_repo: FakePreguntaRepository):
    return PreguntasController(
        CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo),
        CargarPreguntaVerdaderoFalsoUseCase(banco_repo, pregunta_repo),
        EditarPreguntaUseCase(pregunta_repo),
        EliminarPreguntaUseCase(pregunta_repo),
    )


class TestPreguntasController:
    async def test_cargar_pregunta_opcion_multiple_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)

        pregunta, evento = await controller.cargar_pregunta_opcion_multiple(
            banco_id=banco.id,
            texto="¿Cuál es la capital de Entre Ríos?",
            opciones=[
                Opcion(texto="Paraná", es_correcta=True),
                Opcion(texto="Concordia", es_correcta=False),
            ],
            unidad_tematica="Unidad 1",
            tema="Arquitectura",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        )

        assert pregunta.banco_id == banco.id
        assert isinstance(evento, PreguntaCargada)

    async def test_cargar_pregunta_verdadero_falso_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)

        pregunta, evento = await controller.cargar_pregunta_verdadero_falso(
            banco_id=banco.id,
            texto="El sol es una estrella.",
            respuesta_correcta=True,
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        )

        assert pregunta.banco_id == banco.id
        assert pregunta.respuesta_correcta is True
        assert isinstance(evento, PreguntaCargada)

    async def test_eliminar_pregunta_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = _controller(banco_repo, pregunta_repo)
        pregunta, _evento = await controller.cargar_pregunta_verdadero_falso(
            banco_id=banco.id,
            texto="El sol es una estrella.",
            respuesta_correcta=True,
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        )

        eliminada, _evento = await controller.eliminar_pregunta(pregunta_id=pregunta.id)

        assert eliminada.activa is False
