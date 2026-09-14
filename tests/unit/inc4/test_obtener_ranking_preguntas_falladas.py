"""Tests unitarios de `ObtenerRankingPreguntasFalladasUseCase` (US-ADJ-46)."""

from uuid import uuid4

import pytest

from src.analytics.entities.errors import ComisionNoPerteneceAMateria
from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    ComisionResumen,
    EstudianteResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    RespuestaVigente,
)
from src.analytics.entities.ports.pregunta_metadato_consulta_port import (
    MetadatoPreguntaResumen,
    PreguntaMetadatoConsultaPort,
)
from src.analytics.use_cases.obtener_ranking_preguntas_falladas import (
    ObtenerRankingPreguntasFalladasUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(self, respuestas: list[RespuestaVigente]) -> None:
        self._respuestas = respuestas
        self.ultimo_estudiante_ids: list | None = "no llamado"

    async def listar_evaluaciones_finalizadas(self, estudiante_id, materia_id):
        raise NotImplementedError

    async def listar_respuestas_vigentes_de_materia(
        self, materia_id, estudiante_ids
    ) -> list[RespuestaVigente]:
        self.ultimo_estudiante_ids = estudiante_ids
        return self._respuestas

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        raise NotImplementedError

    async def obtener_titulos_actividades(self, actividad_ids):
        raise NotImplementedError

    async def obtener_actividad_resumen(self, actividad_id):
        raise NotImplementedError

    async def listar_estados_de_actividad(self, actividad_id, estudiante_ids):
        raise NotImplementedError


class _ComisionConsultaPortFake(ComisionConsultaPort):
    def __init__(
        self,
        comisiones: list[ComisionResumen] | None = None,
        estudiantes: list[EstudianteResumen] | None = None,
    ) -> None:
        self._comisiones = comisiones or []
        self._estudiantes = estudiantes or []

    async def listar_comisiones_por_materia(self, materia_id) -> list[ComisionResumen]:
        return self._comisiones

    async def listar_estudiantes(self, comision_id) -> list[EstudianteResumen]:
        return self._estudiantes


class _PreguntaMetadatoConsultaPortFake(PreguntaMetadatoConsultaPort):
    def __init__(self, metadatos: dict) -> None:
        self._metadatos = metadatos

    async def obtener_metadatos(self, pregunta_ids) -> dict:
        return {pid: self._metadatos[pid] for pid in pregunta_ids if pid in self._metadatos}


def _use_case(
    respuestas: list[RespuestaVigente],
    metadatos: dict,
    comisiones: list[ComisionResumen] | None = None,
    estudiantes: list[EstudianteResumen] | None = None,
) -> tuple[ObtenerRankingPreguntasFalladasUseCase, _EvaluacionDesempenoConsultaPortFake]:
    evaluacion_desempeno_consulta = _EvaluacionDesempenoConsultaPortFake(respuestas)
    use_case = ObtenerRankingPreguntasFalladasUseCase(
        evaluacion_desempeno_consulta,
        _ComisionConsultaPortFake(comisiones, estudiantes),
        _PreguntaMetadatoConsultaPortFake(metadatos),
    )
    return use_case, evaluacion_desempeno_consulta


def _metadato(unidad: str, tema: str, enunciado: str) -> MetadatoPreguntaResumen:
    return MetadatoPreguntaResumen(unidad_tematica=unidad, tema=tema, enunciado=enunciado)


class TestObtenerRankingPreguntasFalladasUseCase:
    @pytest.mark.asyncio
    async def test_sin_respuestas_devuelve_lista_vacia(self):
        use_case, _ = _use_case(respuestas=[], metadatos={})

        resultado = await use_case.execute(uuid4(), None)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_agrupa_por_pregunta_individual(self):
        pregunta_id = uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=uuid4(), es_correcta=False),
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=uuid4(), es_correcta=True),
        ]
        metadatos = {pregunta_id: _metadato("U1", "Herencia", "¿Qué es herencia?")}
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert len(resultado) == 1
        assert resultado[0].pregunta_id == pregunta_id
        assert resultado[0].enunciado == "¿Qué es herencia?"
        assert resultado[0].unidad_tematica == "U1"
        assert resultado[0].tema == "Herencia"
        assert resultado[0].cantidad_presentaciones == 2
        assert resultado[0].cantidad_fallos == 1
        assert resultado[0].tasa_error == 0.5

    @pytest.mark.asyncio
    async def test_tasa_de_error_prevalece_sobre_conteo_bruto(self):
        pregunta_baja_conteo, pregunta_alto_conteo = uuid4(), uuid4()
        respuestas = [
            RespuestaVigente(
                pregunta_id=pregunta_baja_conteo, estudiante_id=uuid4(), es_correcta=False
            )
        ]
        for _ in range(40):
            respuestas.append(
                RespuestaVigente(
                    pregunta_id=pregunta_alto_conteo, estudiante_id=uuid4(), es_correcta=True
                )
            )
        for _ in range(10):
            respuestas.append(
                RespuestaVigente(
                    pregunta_id=pregunta_alto_conteo, estudiante_id=uuid4(), es_correcta=False
                )
            )
        metadatos = {
            pregunta_baja_conteo: _metadato("U1", "T1", "Pregunta A"),
            pregunta_alto_conteo: _metadato("U1", "T2", "Pregunta B"),
        }
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert [fila.pregunta_id for fila in resultado] == [
            pregunta_baja_conteo,
            pregunta_alto_conteo,
        ]
        assert resultado[0].tasa_error == 1.0
        assert resultado[1].tasa_error == 0.2

    @pytest.mark.asyncio
    async def test_excluye_respuestas_sin_metadato_resoluble(self):
        pregunta_con_metadato, pregunta_sin_metadato = uuid4(), uuid4()
        respuestas = [
            RespuestaVigente(
                pregunta_id=pregunta_con_metadato, estudiante_id=uuid4(), es_correcta=False
            ),
            RespuestaVigente(
                pregunta_id=pregunta_sin_metadato, estudiante_id=uuid4(), es_correcta=False
            ),
        ]
        metadatos = {pregunta_con_metadato: _metadato("U1", "T1", "Pregunta con metadato")}
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert len(resultado) == 1
        assert resultado[0].pregunta_id == pregunta_con_metadato

    @pytest.mark.asyncio
    async def test_sin_comision_id_no_acota_estudiantes(self):
        use_case, evaluacion_desempeno_consulta = _use_case(respuestas=[], metadatos={})

        await use_case.execute(uuid4(), None)

        assert evaluacion_desempeno_consulta.ultimo_estudiante_ids is None

    @pytest.mark.asyncio
    async def test_comision_valida_acota_a_sus_estudiantes(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        use_case, evaluacion_desempeno_consulta = _use_case(
            respuestas=[],
            metadatos={},
            comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
            estudiantes=[estudiante],
        )

        await use_case.execute(materia_id, comision_id)

        assert evaluacion_desempeno_consulta.ultimo_estudiante_ids == [estudiante.id]

    @pytest.mark.asyncio
    async def test_comision_que_no_pertenece_a_la_materia_levanta_error(self):
        materia_id, comision_id = uuid4(), uuid4()
        use_case, _ = _use_case(
            respuestas=[],
            metadatos={},
            comisiones=[ComisionResumen(id=uuid4(), horario="lu 10-12")],
        )

        with pytest.raises(ComisionNoPerteneceAMateria):
            await use_case.execute(materia_id, comision_id)
