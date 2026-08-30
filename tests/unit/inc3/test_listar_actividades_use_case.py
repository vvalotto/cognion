from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)
from src.actividad_evaluativa.use_cases.listar_actividades import ListarActividadesUseCase


class FakeActividadQueryPort(ActividadQueryPort):
    """Consulta de actividades en memoria — devuelve lo que se le precarga en `resumenes`."""

    def __init__(self) -> None:
        self.resumenes: dict[UUID, list[ActividadResumen]] = {}

    async def listar_por_materia(self, materia_id: UUID) -> list[ActividadResumen]:
        return self.resumenes.get(materia_id, [])


def _resumen(materia_id: UUID) -> ActividadResumen:
    apertura = datetime.now(UTC)
    return ActividadResumen(
        id=uuid4(),
        materia_id=materia_id,
        titulo="Parcial 1",
        fecha_apertura=apertura,
        fecha_cierre=apertura + timedelta(days=7),
        cantidad_preguntas=10,
        cantidad_intentos_permitidos=1,
        cerrada_manualmente=False,
        cantidad_evaluaciones_activas=3,
        cantidad_evaluaciones_finalizadas=0,
    )


class TestListarActividadesUseCase:
    async def test_delega_en_el_puerto_de_consulta(self):
        materia_id = uuid4()
        query_port = FakeActividadQueryPort()
        query_port.resumenes[materia_id] = [_resumen(materia_id)]
        use_case = ListarActividadesUseCase(query_port)

        resultado = await use_case.execute(materia_id)

        assert len(resultado) == 1
        assert resultado[0].materia_id == materia_id

    async def test_lista_vacia_si_la_materia_no_tiene_actividades(self):
        query_port = FakeActividadQueryPort()
        use_case = ListarActividadesUseCase(query_port)

        resultado = await use_case.execute(uuid4())

        assert resultado == []
