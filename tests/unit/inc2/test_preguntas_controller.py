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
from tests.unit.inc2._fakes import FakeBancoRepository, FakePreguntaRepository


class TestPreguntasController:
    async def test_cargar_pregunta_opcion_multiple_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        controller = PreguntasController(
            CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo)
        )

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
