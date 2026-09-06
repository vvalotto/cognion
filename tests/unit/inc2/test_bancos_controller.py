import uuid

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.interface_adapters.controllers.bancos_controller import (
    BancosController,
)
from src.banco_preguntas.use_cases.filtrar_banco import FiltrarBancoUseCase
from tests.unit.inc2._fakes import FakeBancoRepository, FakePreguntaRepository


def _pregunta_om(banco_id: uuid.UUID) -> PreguntaPlantillaOpcionMultiple:
    return PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        metadatos=MetadatosPregunta(
            texto="¿Cuál es la capital de Entre Ríos?",
            unidad_tematica="Unidad 1",
            tema="Arquitectura",
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        ),
        opciones=[
            Opcion(texto="Paraná", es_correcta=True),
            Opcion(texto="Concordia", es_correcta=False),
        ],
    )


class TestBancosController:
    async def test_filtrar_preguntas_delega_al_use_case(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)
        pregunta = _pregunta_om(banco.id)
        await pregunta_repo.guardar(pregunta)

        controller = BancosController(FiltrarBancoUseCase(banco_repo, pregunta_repo))

        resultado = await controller.filtrar_preguntas(banco_id=banco.id)

        assert resultado.preguntas == [pregunta]

    async def test_filtrar_preguntas_propaga_filtros(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)
        await pregunta_repo.guardar(_pregunta_om(banco.id))

        controller = BancosController(FiltrarBancoUseCase(banco_repo, pregunta_repo))

        resultado = await controller.filtrar_preguntas(banco_id=banco.id, dificultad="bajo")

        assert resultado.preguntas == []

    async def test_filtrar_preguntas_propaga_pagina_y_tamanio_pagina(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)
        for _ in range(3):
            await pregunta_repo.guardar(_pregunta_om(banco.id))

        controller = BancosController(FiltrarBancoUseCase(banco_repo, pregunta_repo))

        resultado = await controller.filtrar_preguntas(
            banco_id=banco.id, pagina=1, tamanio_pagina=2
        )

        assert len(resultado.preguntas) == 2
        assert resultado.total == 3
