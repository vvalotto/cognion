"""Tests unitarios de `ObtenerDesempenoPorComisionUseCase` (US-ADJ-44)."""

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
from src.analytics.use_cases.obtener_desempeno_por_comision import (
    ObtenerDesempenoPorComisionUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        resumenes_por_estudiante: dict | None = None,
        actividades_abiertas: list | None = None,
    ) -> None:
        self._resumenes_por_estudiante = resumenes_por_estudiante or {}
        self._actividades_abiertas = actividades_abiertas or []

    async def listar_evaluaciones_finalizadas(self, estudiante_id, materia_id):
        return self._resumenes_por_estudiante.get(estudiante_id, [])

    async def listar_respuestas_vigentes_de_materia(self, materia_id, estudiante_ids):
        raise NotImplementedError

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        return self._actividades_abiertas

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


def _resumen(actividad_id, correctas: int, incorrectas: int) -> EvaluacionDesempenoResumen:
    return EvaluacionDesempenoResumen(
        evaluacion_id=uuid4(),
        actividad_id=actividad_id,
        materia_id=uuid4(),
        finalizada_en=datetime(2026, 1, 1, tzinfo=UTC),
        cantidad_correctas=correctas,
        cantidad_incorrectas=incorrectas,
    )


class TestObtenerDesempenoPorComisionUseCase:
    @pytest.mark.asyncio
    async def test_comision_que_no_pertenece_a_la_materia_levanta_error(self):
        materia_id, comision_id = uuid4(), uuid4()
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(comisiones=[ComisionResumen(id=uuid4(), horario="lu 10-12")]),
            _EvaluacionDesempenoConsultaPortFake(),
        )

        with pytest.raises(ComisionNoPerteneceAMateria):
            await use_case.execute(materia_id, comision_id)

    @pytest.mark.asyncio
    async def test_comision_sin_estudiantes_devuelve_lista_vacia(self):
        materia_id, comision_id = uuid4(), uuid4()
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")]
            ),
            _EvaluacionDesempenoConsultaPortFake(),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert resultado == []

    @pytest.mark.asyncio
    async def test_estudiante_sin_evaluaciones_finalizadas_tiene_sin_datos(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Ana Pérez")
        actividad_abierta = uuid4()
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={},
                actividades_abiertas=[actividad_abierta],
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert len(resultado) == 1
        assert resultado[0].estudiante_id == estudiante.id
        assert resultado[0].porcentaje_aciertos_acumulado is None
        assert resultado[0].actividades_pendientes == 1

    @pytest.mark.asyncio
    async def test_estudiante_con_evaluaciones_calcula_porcentaje_y_pendientes(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Juan López")
        actividad_rendida, actividad_pendiente = uuid4(), uuid4()
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={
                    estudiante.id: [_resumen(actividad_rendida, correctas=3, incorrectas=1)]
                },
                actividades_abiertas=[actividad_rendida, actividad_pendiente],
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert resultado[0].porcentaje_aciertos_acumulado == 75.0
        assert resultado[0].actividades_pendientes == 1

    @pytest.mark.asyncio
    async def test_estudiante_finalizo_todas_las_abiertas_no_tiene_pendientes(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Marta Díaz")
        actividad_id = uuid4()
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={
                    estudiante.id: [_resumen(actividad_id, correctas=1, incorrectas=0)]
                },
                actividades_abiertas=[actividad_id],
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert resultado[0].actividades_pendientes == 0

    @pytest.mark.asyncio
    async def test_evaluacion_finalizada_sin_respuestas_no_divide_por_cero(self):
        """Caso límite: `Evaluacion` finalizada sin ninguna pregunta correcta/incorrecta."""
        materia_id, comision_id = uuid4(), uuid4()
        estudiante = EstudianteResumen(id=uuid4(), nombre="Sin Respuestas")
        actividad_id = uuid4()
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante],
            ),
            _EvaluacionDesempenoConsultaPortFake(
                resumenes_por_estudiante={
                    estudiante.id: [_resumen(actividad_id, correctas=0, incorrectas=0)]
                },
            ),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert resultado[0].porcentaje_aciertos_acumulado == 0.0

    @pytest.mark.asyncio
    async def test_multiples_estudiantes_una_fila_por_cada_uno(self):
        materia_id, comision_id = uuid4(), uuid4()
        estudiante_1 = EstudianteResumen(id=uuid4(), nombre="A")
        estudiante_2 = EstudianteResumen(id=uuid4(), nombre="B")
        use_case = ObtenerDesempenoPorComisionUseCase(
            _ComisionConsultaPortFake(
                comisiones=[ComisionResumen(id=comision_id, horario="lu 10-12")],
                estudiantes=[estudiante_1, estudiante_2],
            ),
            _EvaluacionDesempenoConsultaPortFake(),
        )

        resultado = await use_case.execute(materia_id, comision_id)

        assert {fila.estudiante_id for fila in resultado} == {estudiante_1.id, estudiante_2.id}
