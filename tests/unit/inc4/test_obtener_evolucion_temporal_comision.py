"""Tests unitarios de `ObtenerEvolucionTemporalComisionUseCase` (US-ADJ-45)."""

from datetime import UTC, datetime
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
    EvaluacionDesempenoResumen,
)
from src.analytics.use_cases.obtener_evolucion_temporal_comision import (
    ObtenerEvolucionTemporalComisionUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        resumenes_por_estudiante: dict | None = None,
        titulos: dict | None = None,
    ) -> None:
        self._resumenes_por_estudiante = resumenes_por_estudiante or {}
        self._titulos = titulos or {}

    async def listar_evaluaciones_finalizadas(self, estudiante_id, materia_id):
        return self._resumenes_por_estudiante.get(estudiante_id, [])

    async def listar_respuestas_vigentes_de_materia(self, materia_id, estudiante_ids):
        raise NotImplementedError

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        raise NotImplementedError

    async def obtener_titulos_actividades(self, actividad_ids):
        return {aid: self._titulos[aid] for aid in actividad_ids if aid in self._titulos}

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


def _resumen(actividad_id, finalizada_en, correctas, incorrectas) -> EvaluacionDesempenoResumen:
    return EvaluacionDesempenoResumen(
        evaluacion_id=uuid4(),
        actividad_id=actividad_id,
        materia_id=uuid4(),
        finalizada_en=finalizada_en,
        cantidad_correctas=correctas,
        cantidad_incorrectas=incorrectas,
    )


class TestObtenerEvolucionTemporalComisionUseCase:
    @pytest.mark.asyncio
    async def test_comision_que_no_pertenece_a_la_materia_levanta_error(self):
        materia_id, comision_id = uuid4(), uuid4()
        use_case = ObtenerEvolucionTemporalComisionUseCase(
            _ComisionConsultaPortFake(comisiones=[ComisionResumen(id=uuid4(), horario="lu 10-12")]),
            _EvaluacionDesempenoConsultaPortFake(),
        )

        with pytest.raises(ComisionNoPerteneceAMateria):
            await use_case.execute(materia_id, comision_id)

    @pytest.mark.asyncio
    async def test_comision_sin_evaluaciones_finalizadas_devuelve_lista_vacia(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana")
        use_case = ObtenerEvolucionTemporalComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_promedia_solo_entre_quienes_finalizaron_la_actividad(self):
        materia_id, comision_id = uuid4(), uuid4()
        actividad_id = uuid4()
        estudiante_1 = EstudianteResumen(id=uuid4(), nombre="A")
        estudiante_2 = EstudianteResumen(id=uuid4(), nombre="B")
        estudiante_3 = EstudianteResumen(id=uuid4(), nombre="C")
        use_case = ObtenerEvolucionTemporalComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante_1, estudiante_2, estudiante_3],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={
                    estudiante_1.id: [
                        _resumen(actividad_id, datetime(2026, 1, 1, tzinfo=UTC), 4, 0)
                    ],
                    estudiante_2.id: [
                        _resumen(actividad_id, datetime(2026, 1, 1, tzinfo=UTC), 2, 2)
                    ],
                    estudiante_3.id: [],
                }
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert len(resultado) == 1
        assert resultado[0].porcentaje_aciertos_promedio == 75.0

    @pytest.mark.asyncio
    async def test_ordena_por_min_finalizada_en_del_grupo(self):
        materia_id, comision_id = uuid4(), uuid4()
        actividad_vieja, actividad_nueva = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="A")
        use_case = ObtenerEvolucionTemporalComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={
                    estudiante.id: [
                        _resumen(actividad_nueva, datetime(2026, 2, 1, tzinfo=UTC), 1, 0),
                        _resumen(actividad_vieja, datetime(2026, 1, 1, tzinfo=UTC), 1, 0),
                    ]
                }
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert [punto.actividad_id for punto in resultado] == [actividad_vieja, actividad_nueva]

    @pytest.mark.asyncio
    async def test_resuelve_titulo_de_cada_actividad(self):
        materia_id, comision_id = uuid4(), uuid4()
        actividad_id = uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="A")
        use_case = ObtenerEvolucionTemporalComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={
                    estudiante.id: [_resumen(actividad_id, datetime(2026, 1, 1, tzinfo=UTC), 1, 0)]
                },
                titulos={actividad_id: "Parcial 1"},
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert resultado[0].titulo_actividad == "Parcial 1"
