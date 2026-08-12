import uuid

import pytest

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from tests.unit.inc2._fakes import FakeBancoRepository, FakePreguntaRepository


class TestCargarPreguntaVerdaderoFalsoUseCase:
    async def test_carga_pregunta_en_banco_existente(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        use_case = CargarPreguntaVerdaderoFalsoUseCase(banco_repo, pregunta_repo)

        pregunta, evento = await use_case.execute(
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
        assert pregunta_repo.preguntas[pregunta.id] is pregunta
        assert isinstance(evento, PreguntaCargada)
        assert evento.pregunta_id == pregunta.id
        assert evento.banco_id == banco.id

    async def test_carga_pregunta_con_respuesta_falso(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(uuid.uuid4())
        await banco_repo.guardar(banco)
        use_case = CargarPreguntaVerdaderoFalsoUseCase(banco_repo, pregunta_repo)

        pregunta, _evento = await use_case.execute(
            banco_id=banco.id,
            texto="El sol es una estrella.",
            respuesta_correcta=False,
            unidad_tematica="Unidad 1",
            tema="Astronomía",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        )

        assert pregunta.respuesta_correcta is False

    async def test_rechaza_banco_inexistente(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        use_case = CargarPreguntaVerdaderoFalsoUseCase(banco_repo, pregunta_repo)

        with pytest.raises(BancoNoExiste):
            await use_case.execute(
                banco_id=uuid.uuid4(),
                texto="El sol es una estrella.",
                respuesta_correcta=True,
                unidad_tematica="Unidad 1",
                tema="Astronomía",
                dificultad=Dificultad.MEDIO,
                importancia=Importancia.ALTO,
            )

        assert len(pregunta_repo.preguntas) == 0
