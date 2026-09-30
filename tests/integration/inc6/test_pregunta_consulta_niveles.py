"""Integración de `PreguntaConsultaPortInProcess.obtener_niveles` contra la DB real (US-6.2.1)."""

import uuid

import pytest

from src.actividad_evaluativa.entities.errors import PreguntaNoAsignada
from src.actividad_evaluativa.entities.puntaje_en_vivo import NivelesDePregunta, NivelPregunta
from src.actividad_evaluativa.frameworks.adapters.pregunta_consulta_port_in_process import (
    PreguntaConsultaPortInProcess,
)
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)


async def _banco(session) -> Banco:
    materia = Materia.crear(f"Materia {uuid.uuid4()}")
    await SQLAlchemyMateriaRepository(session).guardar(materia)
    banco = Banco.crear(materia.id)
    await SQLAlchemyBancoRepository(session).guardar(banco)
    return banco


def _metadatos(dificultad: Dificultad, importancia: Importancia) -> MetadatosPregunta:
    return MetadatosPregunta(
        texto="¿Pregunta?",
        unidad_tematica="Unidad 1",
        tema="Tema",
        dificultad=dificultad,
        importancia=importancia,
    )


class TestObtenerNiveles:
    async def test_opcion_multiple_devuelve_dificultad_e_importancia(self, session):
        banco = await _banco(session)
        pregunta = PreguntaPlantillaOpcionMultiple.crear(
            banco.id,
            _metadatos(Dificultad.ALTO, Importancia.MEDIO),
            [Opcion(texto="A", es_correcta=True), Opcion(texto="B", es_correcta=False)],
        )
        await SQLAlchemyPreguntaRepository(session).guardar(pregunta)

        niveles = await PreguntaConsultaPortInProcess(session).obtener_niveles(pregunta.id)

        assert niveles == NivelesDePregunta(NivelPregunta.ALTO, NivelPregunta.MEDIO)

    async def test_verdadero_falso_devuelve_dificultad_e_importancia(self, session):
        banco = await _banco(session)
        pregunta = PreguntaPlantillaVerdaderoFalso.crear(
            banco.id, _metadatos(Dificultad.BAJO, Importancia.ALTO), True
        )
        await SQLAlchemyPreguntaRepository(session).guardar(pregunta)

        niveles = await PreguntaConsultaPortInProcess(session).obtener_niveles(pregunta.id)

        assert niveles == NivelesDePregunta(NivelPregunta.BAJO, NivelPregunta.ALTO)

    async def test_pregunta_inexistente_lanza_pregunta_no_asignada(self, session):
        with pytest.raises(PreguntaNoAsignada):
            await PreguntaConsultaPortInProcess(session).obtener_niveles(uuid.uuid4())
