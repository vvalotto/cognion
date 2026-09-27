"""Tests unitarios de `ObtenerDesempenoEstudianteUseCase` (US-4.1.2, ampliado en US-ADJ-56)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    ComisionResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)
from src.analytics.entities.ports.sesion_en_vivo_desempeno_consulta_port import (
    SesionEnVivoDesempenoConsultaPort,
    SesionEnVivoDesempenoResumen,
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

    async def listar_respuestas_vigentes_de_materia(self, materia_id, estudiante_ids):
        raise NotImplementedError

    async def listar_actividades_abiertas(self, materia_id, comision_id):
        raise NotImplementedError

    async def obtener_titulos_actividades(self, actividad_ids):
        raise NotImplementedError

    async def obtener_actividad_resumen(self, actividad_id):
        raise NotImplementedError

    async def listar_estados_de_actividad(self, actividad_id, estudiante_ids):
        raise NotImplementedError


class _SesionEnVivoDesempenoConsultaPortFake(SesionEnVivoDesempenoConsultaPort):
    """Fake del puerto de `US-ADJ-56` — devuelve una lista fija, sin tocar la base de datos."""

    def __init__(self, resumenes: list[SesionEnVivoDesempenoResumen] | None = None) -> None:
        self._resumenes = resumenes or []

    async def listar_sesiones_finalizadas(
        self, estudiante_id, materia_id
    ) -> list[SesionEnVivoDesempenoResumen]:
        return self._resumenes


class _ComisionConsultaPortFake(ComisionConsultaPort):
    """Fake del puerto de comisiones — devuelve una lista fija de `ComisionResumen`."""

    def __init__(self, comisiones: list[ComisionResumen] | None = None) -> None:
        self._comisiones = comisiones or []

    async def listar_comisiones_por_materia(self, materia_id) -> list[ComisionResumen]:
        return self._comisiones

    async def listar_estudiantes(self, comision_id):
        raise NotImplementedError


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


def _resumen_en_vivo(
    comision_id,
    finalizada_en: datetime,
    correctas: int = 0,
    incorrectas: int = 0,
    puntaje_final: int = 0,
    posicion: int = 1,
    total_participantes: int = 1,
    cantidad_preguntas: int = 5,
) -> SesionEnVivoDesempenoResumen:
    return SesionEnVivoDesempenoResumen(
        sesion_id=uuid4(),
        comision_id=comision_id,
        materia_id=uuid4(),
        finalizada_en=finalizada_en,
        cantidad_preguntas=cantidad_preguntas,
        cantidad_correctas=correctas,
        cantidad_incorrectas=incorrectas,
        puntaje_final=puntaje_final,
        posicion=posicion,
        total_participantes=total_participantes,
    )


def _use_case(
    resumenes: list[EvaluacionDesempenoResumen] | None = None,
    resumenes_en_vivo: list[SesionEnVivoDesempenoResumen] | None = None,
    comisiones: list[ComisionResumen] | None = None,
) -> ObtenerDesempenoEstudianteUseCase:
    return ObtenerDesempenoEstudianteUseCase(
        _EvaluacionDesempenoConsultaPortFake(resumenes or []),
        _SesionEnVivoDesempenoConsultaPortFake(resumenes_en_vivo),
        _ComisionConsultaPortFake(comisiones),
    )


class TestObtenerDesempenoEstudianteUseCase:
    @pytest.mark.asyncio
    async def test_detalle_ordenado_por_finalizada_en_descendente(self):
        mas_antigua = _resumen(datetime(2026, 1, 1, tzinfo=UTC), 5, 3)
        mas_reciente = _resumen(datetime(2026, 1, 2, tzinfo=UTC), 8, 2)
        use_case = _use_case([mas_antigua, mas_reciente])

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
        use_case = _use_case(resumenes)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.resumen.total_correctas == 13
        assert resultado.resumen.total_incorrectas == 5
        assert resultado.resumen.cantidad_evaluaciones == 2

    @pytest.mark.asyncio
    async def test_porcentaje_acierto_calculado_sobre_total_de_respuestas(self):
        resumenes = [_resumen(datetime(2026, 1, 1, tzinfo=UTC), 8, 2)]
        use_case = _use_case(resumenes)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.resumen.porcentaje_acierto == 80

    @pytest.mark.asyncio
    async def test_sin_evaluaciones_finalizadas_devuelve_todo_en_cero(self):
        use_case = _use_case([])

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

            async def listar_respuestas_vigentes_de_materia(self, materia_id, estudiante_ids):
                raise NotImplementedError

            async def listar_actividades_abiertas(self, materia_id, comision_id):
                raise NotImplementedError

            async def obtener_titulos_actividades(self, actividad_ids):
                raise NotImplementedError

            async def obtener_actividad_resumen(self, actividad_id):
                raise NotImplementedError

            async def listar_estados_de_actividad(self, actividad_id, estudiante_ids):
                raise NotImplementedError

        use_case = ObtenerDesempenoEstudianteUseCase(
            _PuertoQueRegistraLlamada(),
            _SesionEnVivoDesempenoConsultaPortFake(),
            _ComisionConsultaPortFake(),
        )
        await use_case.execute(estudiante_id, materia_id)

        assert recibidos["estudiante_id"] == estudiante_id
        assert recibidos["materia_id"] == materia_id

    @pytest.mark.asyncio
    async def test_evaluacion_del_pasado_lejano_no_rompe_el_orden(self):
        hace_un_anio = datetime.now(UTC) - timedelta(days=365)
        ahora = datetime.now(UTC)
        antigua = _resumen(hace_un_anio, 1, 0)
        reciente = _resumen(ahora, 2, 0)
        use_case = _use_case([antigua, reciente])

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.evaluaciones[0].evaluacion_id == reciente.evaluacion_id
        assert resultado.evaluaciones[1].evaluacion_id == antigua.evaluacion_id


class TestSesionesEnVivo:
    """Tests de la sección de sesiones en vivo (`US-ADJ-56`)."""

    @pytest.mark.asyncio
    async def test_sin_sesiones_en_vivo_devuelve_lista_vacia(self):
        use_case = _use_case()

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.sesiones_en_vivo == []

    @pytest.mark.asyncio
    async def test_resumen_de_periodo_abierto_no_se_ve_afectado_por_las_sesiones_en_vivo(self):
        comision_id = uuid4()
        resumenes = [_resumen(datetime(2026, 1, 1, tzinfo=UTC), 8, 2)]
        resumenes_en_vivo = [
            _resumen_en_vivo(comision_id, datetime(2026, 1, 3, tzinfo=UTC), correctas=3)
        ]
        comisiones = [ComisionResumen(id=comision_id, horario="Lunes 14-16hs")]
        use_case = _use_case(resumenes, resumenes_en_vivo, comisiones)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.resumen.total_correctas == 8
        assert resultado.resumen.total_incorrectas == 2
        assert resultado.resumen.cantidad_evaluaciones == 1
        assert len(resultado.sesiones_en_vivo) == 1

    @pytest.mark.asyncio
    async def test_sesiones_en_vivo_ordenadas_por_finalizada_en_descendente(self):
        comision_id = uuid4()
        mas_antigua = _resumen_en_vivo(comision_id, datetime(2026, 1, 1, tzinfo=UTC))
        mas_reciente = _resumen_en_vivo(comision_id, datetime(2026, 1, 5, tzinfo=UTC))
        comisiones = [ComisionResumen(id=comision_id, horario="Lunes 14-16hs")]
        use_case = _use_case(resumenes_en_vivo=[mas_antigua, mas_reciente], comisiones=comisiones)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert [s.sesion_id for s in resultado.sesiones_en_vivo] == [
            mas_reciente.sesion_id,
            mas_antigua.sesion_id,
        ]

    @pytest.mark.asyncio
    async def test_resuelve_el_horario_de_la_comision(self):
        comision_id = uuid4()
        resumen_vivo = _resumen_en_vivo(comision_id, datetime(2026, 1, 1, tzinfo=UTC))
        comisiones = [ComisionResumen(id=comision_id, horario="Martes 18-20hs")]
        use_case = _use_case(resumenes_en_vivo=[resumen_vivo], comisiones=comisiones)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.sesiones_en_vivo[0].comision_horario == "Martes 18-20hs"

    @pytest.mark.asyncio
    async def test_comision_no_encontrada_deja_horario_vacio(self):
        resumen_vivo = _resumen_en_vivo(uuid4(), datetime(2026, 1, 1, tzinfo=UTC))
        use_case = _use_case(resumenes_en_vivo=[resumen_vivo], comisiones=[])

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado.sesiones_en_vivo[0].comision_horario == ""

    @pytest.mark.asyncio
    async def test_conserva_correctas_incorrectas_puntaje_y_posicion(self):
        comision_id = uuid4()
        resumen_vivo = _resumen_en_vivo(
            comision_id,
            datetime(2026, 1, 1, tzinfo=UTC),
            correctas=7,
            incorrectas=3,
            puntaje_final=1200,
            posicion=3,
            total_participantes=14,
            cantidad_preguntas=10,
        )
        comisiones = [ComisionResumen(id=comision_id, horario="Lunes 14-16hs")]
        use_case = _use_case(resumenes_en_vivo=[resumen_vivo], comisiones=comisiones)

        resultado = await use_case.execute(uuid4(), uuid4())

        detalle = resultado.sesiones_en_vivo[0]
        assert detalle.cantidad_correctas == 7
        assert detalle.cantidad_incorrectas == 3
        assert detalle.puntaje_final == 1200
        assert detalle.posicion == 3
        assert detalle.total_participantes == 14
        assert detalle.cantidad_preguntas == 10
