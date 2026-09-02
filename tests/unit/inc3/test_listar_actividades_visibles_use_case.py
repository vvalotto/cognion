from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)
from src.actividad_evaluativa.entities.ports.evaluacion_estudiante_query_port import (
    EvaluacionEstudianteQueryPort,
)
from src.actividad_evaluativa.use_cases.listar_actividades_visibles import (
    ListarActividadesVisiblesUseCase,
)


class FakeActividadQueryPort(ActividadQueryPort):
    def __init__(self) -> None:
        self.resumenes: dict[UUID, list[ActividadResumen]] = {}

    async def listar_por_materia(self, materia_id: UUID) -> list[ActividadResumen]:
        return self.resumenes.get(materia_id, [])

    async def obtener(self, actividad_id: UUID) -> ActividadResumen | None:
        for resumenes in self.resumenes.values():
            for resumen in resumenes:
                if resumen.id == actividad_id:
                    return resumen
        return None


class FakeEvaluacionEstudianteQueryPort(EvaluacionEstudianteQueryPort):
    def __init__(self) -> None:
        self.finalizadas: set[UUID] = set()

    async def existentes_finalizadas(self, evaluacion_ids: list[UUID]) -> set[UUID]:
        return {eid for eid in evaluacion_ids if eid in self.finalizadas}


def _resumen(
    materia_id: UUID,
    ahora: datetime,
    *,
    fecha_apertura: datetime | None = None,
    fecha_cierre: datetime | None = None,
    cerrada_manualmente: bool = False,
    actividad_id: UUID | None = None,
) -> ActividadResumen:
    return ActividadResumen(
        id=actividad_id or uuid4(),
        materia_id=materia_id,
        titulo="Parcial 1",
        fecha_apertura=fecha_apertura or (ahora - timedelta(days=1)),
        fecha_cierre=fecha_cierre or (ahora + timedelta(days=7)),
        cantidad_preguntas=10,
        cantidad_intentos_permitidos=1,
        cerrada_manualmente=cerrada_manualmente,
        cantidad_evaluaciones_activas=1,
        cantidad_evaluaciones_finalizadas=0,
    )


class TestListarActividadesVisiblesUseCase:
    async def test_pendiente_dentro_del_periodo_sin_evaluacion_finalizada(self):
        materia_id = uuid4()
        estudiante_id = uuid4()
        ahora = datetime.now(UTC)
        actividad_query = FakeActividadQueryPort()
        actividad_query.resumenes[materia_id] = [_resumen(materia_id, ahora)]
        evaluacion_query = FakeEvaluacionEstudianteQueryPort()
        use_case = ListarActividadesVisiblesUseCase(actividad_query, evaluacion_query)

        resultado = await use_case.execute(materia_id, estudiante_id)

        assert len(resultado) == 1
        assert resultado[0].estado == "pendiente"
        assert resultado[0].evaluacion_id is None

    async def test_todavia_no_abrio_con_fecha_apertura_futura(self):
        materia_id = uuid4()
        estudiante_id = uuid4()
        ahora = datetime.now(UTC)
        actividad_query = FakeActividadQueryPort()
        actividad_query.resumenes[materia_id] = [
            _resumen(
                materia_id,
                ahora,
                fecha_apertura=ahora + timedelta(days=1),
                fecha_cierre=ahora + timedelta(days=8),
            )
        ]
        evaluacion_query = FakeEvaluacionEstudianteQueryPort()
        use_case = ListarActividadesVisiblesUseCase(actividad_query, evaluacion_query)

        resultado = await use_case.execute(materia_id, estudiante_id)

        assert resultado[0].estado == "todavia_no_abrio"

    async def test_finalizada_cuando_el_estudiante_ya_tiene_evaluacion_finalizada(self):
        materia_id = uuid4()
        estudiante_id = uuid4()
        ahora = datetime.now(UTC)
        actividad_id = uuid4()
        actividad_query = FakeActividadQueryPort()
        actividad_query.resumenes[materia_id] = [
            _resumen(materia_id, ahora, actividad_id=actividad_id)
        ]
        evaluacion_query = FakeEvaluacionEstudianteQueryPort()
        evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)
        evaluacion_query.finalizadas.add(evaluacion_id)
        use_case = ListarActividadesVisiblesUseCase(actividad_query, evaluacion_query)

        resultado = await use_case.execute(materia_id, estudiante_id)

        assert resultado[0].estado == "finalizada"
        assert resultado[0].evaluacion_id == evaluacion_id

    async def test_cerrada_sin_rendir_se_muestra_como_pendiente(self):
        """No hay badge propio para 'cerrada sin rendir' — mismo prototipo aprobado (`US-3.4.5`)."""
        materia_id = uuid4()
        estudiante_id = uuid4()
        ahora = datetime.now(UTC)
        actividad_query = FakeActividadQueryPort()
        actividad_query.resumenes[materia_id] = [
            _resumen(
                materia_id,
                ahora,
                fecha_apertura=ahora - timedelta(days=8),
                fecha_cierre=ahora - timedelta(days=1),
            )
        ]
        evaluacion_query = FakeEvaluacionEstudianteQueryPort()
        use_case = ListarActividadesVisiblesUseCase(actividad_query, evaluacion_query)

        resultado = await use_case.execute(materia_id, estudiante_id)

        assert resultado[0].estado == "pendiente"

    async def test_lista_vacia_si_la_materia_no_tiene_actividades(self):
        actividad_query = FakeActividadQueryPort()
        evaluacion_query = FakeEvaluacionEstudianteQueryPort()
        use_case = ListarActividadesVisiblesUseCase(actividad_query, evaluacion_query)

        resultado = await use_case.execute(uuid4(), uuid4())

        assert resultado == []
