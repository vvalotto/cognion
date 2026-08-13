import uuid

import pytest

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.use_cases.filtrar_banco import FiltrarBancoUseCase
from tests.unit.inc2._fakes import FakeBancoRepository, FakePreguntaRepository


def _pregunta_om(
    banco_id: uuid.UUID,
    unidad: str = "Unidad 1",
    tema: str = "Arquitectura",
    dificultad: Dificultad = Dificultad.MEDIO,
    importancia: Importancia = Importancia.ALTO,
) -> PreguntaPlantillaOpcionMultiple:
    return PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        texto="¿Cuál es la capital de Entre Ríos?",
        opciones=[
            Opcion(texto="Paraná", es_correcta=True),
            Opcion(texto="Concordia", es_correcta=False),
        ],
        unidad_tematica=unidad,
        tema=tema,
        dificultad=dificultad,
        importancia=importancia,
    )


def _pregunta_vf(
    banco_id: uuid.UUID,
    unidad: str = "Unidad 1",
    tema: str = "Astronomía",
    dificultad: Dificultad = Dificultad.MEDIO,
    importancia: Importancia = Importancia.ALTO,
) -> PreguntaPlantillaVerdaderoFalso:
    return PreguntaPlantillaVerdaderoFalso.crear(
        banco_id=banco_id,
        texto="El sol es una estrella.",
        respuesta_correcta=True,
        unidad_tematica=unidad,
        tema=tema,
        dificultad=dificultad,
        importancia=importancia,
    )


class TestFiltrarBancoUseCase:
    async def test_filtro_combinado_dificultad_e_importancia(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)

        match = _pregunta_om(banco.id, dificultad=Dificultad.ALTO, importancia=Importancia.ALTO)
        otra_dificultad = _pregunta_vf(
            banco.id, dificultad=Dificultad.BAJO, importancia=Importancia.ALTO
        )
        await pregunta_repo.guardar(match)
        await pregunta_repo.guardar(otra_dificultad)

        use_case = FiltrarBancoUseCase(banco_repo, pregunta_repo)
        resultado = await use_case.execute(
            banco_id=banco.id, dificultad=Dificultad.ALTO, importancia=Importancia.ALTO
        )

        assert resultado == [match]

    async def test_sin_filtros_adicionales_devuelve_solo_activas(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)

        activas = [_pregunta_om(banco.id) for _ in range(5)]
        for pregunta in activas:
            await pregunta_repo.guardar(pregunta)
        inactiva = _pregunta_vf(banco.id)
        inactiva.activa = False
        await pregunta_repo.guardar(inactiva)

        use_case = FiltrarBancoUseCase(banco_repo, pregunta_repo)
        resultado = await use_case.execute(banco_id=banco.id)

        assert len(resultado) == 5
        assert inactiva not in resultado

    async def test_ningun_resultado(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)
        await pregunta_repo.guardar(_pregunta_om(banco.id, dificultad=Dificultad.ALTO))

        use_case = FiltrarBancoUseCase(banco_repo, pregunta_repo)
        resultado = await use_case.execute(banco_id=banco.id, dificultad=Dificultad.BAJO)

        assert resultado == []

    async def test_rechaza_banco_inexistente(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        use_case = FiltrarBancoUseCase(banco_repo, pregunta_repo)

        with pytest.raises(BancoNoExiste):
            await use_case.execute(banco_id=uuid.uuid4())

    async def test_filtra_por_unidad_y_tema(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)

        match = _pregunta_om(banco.id, unidad="Unidad 2", tema="Testing")
        otra_unidad = _pregunta_om(banco.id, unidad="Unidad 1", tema="Testing")
        await pregunta_repo.guardar(match)
        await pregunta_repo.guardar(otra_unidad)

        use_case = FiltrarBancoUseCase(banco_repo, pregunta_repo)
        resultado = await use_case.execute(banco_id=banco.id, unidad="Unidad 2", tema="Testing")

        assert resultado == [match]

    async def test_no_incluye_preguntas_de_otro_banco(self):
        banco_repo = FakeBancoRepository()
        pregunta_repo = FakePreguntaRepository()
        banco = Banco.crear(materia_id=uuid.uuid4())
        otro_banco = Banco.crear(materia_id=uuid.uuid4())
        await banco_repo.guardar(banco)
        await banco_repo.guardar(otro_banco)

        de_otro_banco = _pregunta_om(otro_banco.id)
        await pregunta_repo.guardar(de_otro_banco)

        use_case = FiltrarBancoUseCase(banco_repo, pregunta_repo)
        resultado = await use_case.execute(banco_id=banco.id)

        assert resultado == []
