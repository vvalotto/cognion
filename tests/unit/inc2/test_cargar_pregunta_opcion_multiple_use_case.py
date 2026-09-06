import uuid

import pytest

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import BancoNoExiste, OpcionesInvalidas
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from tests.unit.inc2._fakes import FakeBancoRepository, FakePreguntaRepository


def _opciones_validas() -> list[Opcion]:
    return [
        Opcion(texto="Paraná", es_correcta=True),
        Opcion(texto="Concordia", es_correcta=False),
        Opcion(texto="Gualeguaychú", es_correcta=False),
    ]


class TestCargarPreguntaOpcionMultipleUseCase:
    async def test_carga_pregunta_en_banco_existente(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        use_case = CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo)

        pregunta, evento = await use_case.execute(
            banco_id=banco.id,
            metadatos=MetadatosPregunta(
                texto="¿Cuál es la capital de Entre Ríos?",
                unidad_tematica="Unidad 1",
                tema="Arquitectura",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            ),
            opciones=_opciones_validas(),
        )

        assert pregunta.banco_id == banco.id
        assert pregunta_repo.preguntas[pregunta.id] is pregunta
        assert isinstance(evento, PreguntaCargada)
        assert evento.pregunta_id == pregunta.id
        assert evento.banco_id == banco.id

    async def test_rechaza_banco_inexistente(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        use_case = CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo)

        with pytest.raises(BancoNoExiste):
            await use_case.execute(
                banco_id=uuid.uuid4(),
                metadatos=MetadatosPregunta(
                    texto="¿Cuál es la capital de Entre Ríos?",
                    unidad_tematica="Unidad 1",
                    tema="Arquitectura",
                    dificultad=Dificultad.MEDIO,
                    importancia=Importancia.ALTO,
                ),
                opciones=_opciones_validas(),
            )

        assert len(pregunta_repo.preguntas) == 0

    async def test_propaga_opciones_invalidas_sin_persistir(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        use_case = CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo)

        with pytest.raises(OpcionesInvalidas):
            await use_case.execute(
                banco_id=banco.id,
                metadatos=MetadatosPregunta(
                    texto="¿Cuál es la capital de Entre Ríos?",
                    unidad_tematica="Unidad 1",
                    tema="Arquitectura",
                    dificultad=Dificultad.MEDIO,
                    importancia=Importancia.ALTO,
                ),
                opciones=[Opcion(texto="Paraná", es_correcta=True)],
            )

        assert len(pregunta_repo.preguntas) == 0
