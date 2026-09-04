"""Tests unitarios de `ObtenerDesempenoEstudianteUseCase` (US-4.1.2)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import (
    ObtenerDesempenoEstudianteUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    """Fake del puerto de `US-4.1.1` — devuelve una lista fija, sin tocar la base de datos."""

    def __init__(self, resumenes: list[EvaluacionDesempenoResumen]) -> None:
        self._resumenes = resumenes

    async def listar_evaluaciones_finalizadas(
        self, estudiante_id, materia_id
    ) -> list[EvaluacionDesempenoResumen]:
        return self._resumenes


def _resumen(
    finalizada_en: datetime, correctas: int, incorrectas: int
) -> EvaluacionDesempenoResumen:
    return EvaluacionDesempenoResumen(
        evaluacion_id=uuid4(),
        actividad_id=uuid4(),
        materia_id=uuid4(),
        finalizada_en=finalizada_en,
        cantidad_correctas=correctas,
        cantidad_incorrectas=incorrectas,
    )


class TestObtenerDesempenoEstudianteUseCase:
    @pytest.mark.asyncio
    async def test_detalle_ordenado_por_finalizada_en_descendente(self):
        mas_antigua = _resumen(datetime(2026, 1, 1, tzinfo=UTC), 5, 3)
        mas_reciente = _resumen(datetime(2026, 1, 2, tzinfo=UTC), 8, 2)
        puerto = _EvaluacionDesempenoConsultaPortFake([mas_antigua, mas_reciente])
        use_case = ObtenerDesempenoEstudianteUseCase(puerto)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert [e.evaluacion_id for e in resultado.evaluaciones] == [
            mas_reciente.evaluacion_id,
            mas_antigua.evaluacion_id,
        ]

    @pytest.mark.asyncio
    async def test_resumen_acumula_correctas_incorrectas_y_cantidad(self):
        resumenes = [
            _resumen(datetime(2026, 1, 1, tzinfo=UTC), 8, 2),
            _resumen(datetime(2026, 1, 2, tzinfo=UTC), 5, 3),
        ]
        use_case = ObtenerDesempenoEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake(resumenes)
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.resumen.total_correctas == 13
        assert resultado.resumen.total_incorrectas == 5
        assert resultado.resumen.cantidad_evaluaciones == 2

    @pytest.mark.asyncio
    async def test_porcentaje_acierto_calculado_sobre_total_de_respuestas(self):
        resumenes = [_resumen(datetime(2026, 1, 1, tzinfo=UTC), 8, 2)]
        use_case = ObtenerDesempenoEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake(resumenes)
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.resumen.porcentaje_acierto == 80

    @pytest.mark.asyncio
    async def test_sin_evaluaciones_finalizadas_devuelve_todo_en_cero(self):
        use_case = ObtenerDesempenoEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake([])
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.evaluaciones == []
        assert resultado.resumen.total_correctas == 0
        assert resultado.resumen.total_incorrectas == 0
        assert resultado.resumen.porcentaje_acierto == 0
        assert resultado.resumen.cantidad_evaluaciones == 0

    @pytest.mark.asyncio
    async def test_delega_estudiante_id_y_materia_id_al_puerto(self):
        estudiante_id = uuid4()
        materia_id = uuid4()
        recibidos: dict[str, object] = {}

        class _PuertoQueRegistraLlamada(EvaluacionDesempenoConsultaPort):
            async def listar_evaluaciones_finalizadas(self, estudiante_id, materia_id):
                recibidos["estudiante_id"] = estudiante_id
                recibidos["materia_id"] = materia_id
                return []

        use_case = ObtenerDesempenoEstudianteUseCase(_PuertoQueRegistraLlamada())
        await use_case.execute(estudiante_id, materia_id)

        assert recibidos["estudiante_id"] == estudiante_id
        assert recibidos["materia_id"] == materia_id

    @pytest.mark.asyncio
    async def test_evaluacion_del_pasado_lejano_no_rompe_el_orden(self):
        hace_un_anio = datetime.now(UTC) - timedelta(days=365)
        ahora = datetime.now(UTC)
        antigua = _resumen(hace_un_anio, 1, 0)
        reciente = _resumen(ahora, 2, 0)
        use_case = ObtenerDesempenoEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake([antigua, reciente])
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.evaluaciones[0].evaluacion_id == reciente.evaluacion_id
        assert resultado.evaluaciones[1].evaluacion_id == antigua.evaluacion_id
