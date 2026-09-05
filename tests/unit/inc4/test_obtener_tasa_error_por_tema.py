"""Tests unitarios de `ObtenerTasaErrorPorTemaUseCase` (US-4.2.4)."""

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
from src.analytics.use_cases.obtener_tasa_error_por_tema import (
    ObtenerTasaErrorPorTemaUseCase,
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
) -> tuple[ObtenerTasaErrorPorTemaUseCase, _EvaluacionDesempenoConsultaPortFake]:
    evaluacion_desempeno_consulta = _EvaluacionDesempenoConsultaPortFake(respuestas)
    use_case = ObtenerTasaErrorPorTemaUseCase(
        evaluacion_desempeno_consulta,
        _ComisionConsultaPortFake(comisiones, estudiantes),
        _PreguntaMetadatoConsultaPortFake(metadatos),
    )
    return use_case, evaluacion_desempeno_consulta


class TestObtenerTasaErrorPorTemaUseCase:
    @pytest.mark.asyncio
    async def test_sin_respuestas_devuelve_lista_vacia(self):
        use_case, _ = _use_case(respuestas=[], metadatos={})

        resultado = await use_case.execute(uuid4(), None)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_agrupa_por_unidad_tematica_y_tema(self):
        pregunta_a, pregunta_b = uuid4(), uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_a, estudiante_id=uuid4(), es_correcta=False),
            RespuestaVigente(pregunta_id=pregunta_b, estudiante_id=uuid4(), es_correcta=True),
        ]
        metadatos = {
            pregunta_a: MetadatoPreguntaResumen(unidad_tematica="U1", tema="Herencia"),
            pregunta_b: MetadatoPreguntaResumen(unidad_tematica="U1", tema="Herencia"),
        }
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert len(resultado) == 1
        assert resultado[0].unidad_tematica == "U1"
        assert resultado[0].tema == "Herencia"
        assert resultado[0].cantidad_respuestas == 2
        assert resultado[0].cantidad_incorrectas == 1
        assert resultado[0].tasa_error == 0.5

    @pytest.mark.asyncio
    async def test_tasa_error_nunca_divide_por_cero(self):
        pregunta_id = uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_id, estudiante_id=uuid4(), es_correcta=True)
        ]
        metadatos = {pregunta_id: MetadatoPreguntaResumen(unidad_tematica="U1", tema="T1")}
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert resultado[0].cantidad_respuestas == 1
        assert resultado[0].cantidad_incorrectas == 0
        assert resultado[0].tasa_error == 0.0

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
        metadatos = {
            pregunta_con_metadato: MetadatoPreguntaResumen(unidad_tematica="U1", tema="T1")
        }
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert len(resultado) == 1
        assert resultado[0].cantidad_respuestas == 1

    @pytest.mark.asyncio
    async def test_ordena_por_tasa_error_descendente(self):
        pregunta_baja, pregunta_alta = uuid4(), uuid4()
        respuestas = [
            RespuestaVigente(pregunta_id=pregunta_baja, estudiante_id=uuid4(), es_correcta=True),
            RespuestaVigente(pregunta_id=pregunta_alta, estudiante_id=uuid4(), es_correcta=False),
        ]
        metadatos = {
            pregunta_baja: MetadatoPreguntaResumen(unidad_tematica="U1", tema="BajaTasa"),
            pregunta_alta: MetadatoPreguntaResumen(unidad_tematica="U2", tema="AltaTasa"),
        }
        use_case, _ = _use_case(respuestas, metadatos)

        resultado = await use_case.execute(uuid4(), None)

        assert [tasa.tema for tasa in resultado] == ["AltaTasa", "BajaTasa"]

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
