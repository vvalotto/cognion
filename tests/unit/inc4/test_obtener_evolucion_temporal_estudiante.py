"""Tests unitarios de `ObtenerEvolucionTemporalEstudianteUseCase` (US-ADJ-45)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)
from src.analytics.use_cases.obtener_evolucion_temporal_estudiante import (
    ObtenerEvolucionTemporalEstudianteUseCase,
)


class _EvaluacionDesempenoConsultaPortFake(EvaluacionDesempenoConsultaPort):
    def __init__(
        self,
        resumenes: list[EvaluacionDesempenoResumen] | None = None,
        titulos: dict | None = None,
    ) -> None:
        self._resumenes = resumenes or []
        self._titulos = titulos or {}

    async def listar_evaluaciones_finalizadas(self, estudiante_id, materia_id):
        return self._resumenes

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


def _resumen(actividad_id, finalizada_en, correctas, incorrectas) -> EvaluacionDesempenoResumen:
    return EvaluacionDesempenoResumen(
        evaluacion_id=uuid4(),
        actividad_id=actividad_id,
        materia_id=uuid4(),
        finalizada_en=finalizada_en,
        cantidad_correctas=correctas,
        cantidad_incorrectas=incorrectas,
    )


class TestObtenerEvolucionTemporalEstudianteUseCase:
    @pytest.mark.asyncio
    async def test_sin_evaluaciones_finalizadas_devuelve_lista_vacia(self):
        use_case = ObtenerEvolucionTemporalEstudianteUseCase(_EvaluacionDesempenoConsultaPortFake())

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado == []

    @pytest.mark.asyncio
    async def test_ordena_por_finalizada_en_ascendente(self):
        actividad_vieja, actividad_nueva = uuid4(), uuid4()
        resumenes = [
            _resumen(actividad_nueva, datetime(2026, 2, 1, tzinfo=UTC), 1, 0),
            _resumen(actividad_vieja, datetime(2026, 1, 1, tzinfo=UTC), 1, 0),
        ]
        use_case = ObtenerEvolucionTemporalEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake(resumenes)
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert [punto.actividad_id for punto in resultado] == [actividad_vieja, actividad_nueva]

    @pytest.mark.asyncio
    async def test_resuelve_titulo_de_cada_actividad(self):
        actividad_id = uuid4()
        resumenes = [_resumen(actividad_id, datetime(2026, 1, 1, tzinfo=UTC), 3, 1)]
        use_case = ObtenerEvolucionTemporalEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake(
                resumenes, titulos={actividad_id: "Primer parcial"}
            )
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado[0].titulo_actividad == "Primer parcial"
        assert resultado[0].porcentaje_acierto == 75

    @pytest.mark.asyncio
    async def test_actividad_sin_titulo_resuelto_usa_cadena_vacia(self):
        actividad_id = uuid4()
        resumenes = [_resumen(actividad_id, datetime(2026, 1, 1, tzinfo=UTC), 1, 0)]
        use_case = ObtenerEvolucionTemporalEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake(resumenes, titulos={})
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado[0].titulo_actividad == ""

    @pytest.mark.asyncio
    async def test_porcentaje_cero_sin_respuestas(self):
        actividad_id = uuid4()
        resumenes = [_resumen(actividad_id, datetime(2026, 1, 1, tzinfo=UTC), 0, 0)]
        use_case = ObtenerEvolucionTemporalEstudianteUseCase(
            _EvaluacionDesempenoConsultaPortFake(resumenes)
        )

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado[0].porcentaje_acierto == 0
