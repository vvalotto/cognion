"""Tests unitarios de `NotificarAperturaUseCase` (US-5.1.2)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort
from src.notificaciones.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    DestinatarioNotificacion,
)
from src.notificaciones.use_cases.notificar_apertura import NotificarAperturaUseCase


class FakeComisionConsultaPort(ComisionConsultaPort):
    """Doble en memoria — devuelve lo que se le precarga en los diccionarios."""

    def __init__(self) -> None:
        self.comisiones_por_materia: dict = {}
        self.destinatarios_por_comisiones: dict = {}

    async def listar_comisiones_por_materia(self, materia_id):
        return self.comisiones_por_materia.get(materia_id, [])

    async def listar_destinatarios(self, comision_ids):
        clave = tuple(sorted(comision_ids, key=str))
        return self.destinatarios_por_comisiones.get(clave, [])


class FakeCanalEnvioPort(CanalEnvioPort):
    """Doble en memoria — registra cada envío; puede fallar para destinatarios elegidos."""

    def __init__(self) -> None:
        self.enviados: list[tuple[str, str, str]] = []
        self.falla_para: set[str] = set()

    async def enviar(self, destinatario_email: str, asunto: str, cuerpo: str) -> None:
        if destinatario_email in self.falla_para:
            raise ConnectionError("SMTP no disponible")
        self.enviados.append((destinatario_email, asunto, cuerpo))


def _fechas() -> tuple[datetime, datetime]:
    apertura = datetime.now(UTC)
    return apertura, apertura + timedelta(days=7)


def _destinatario(nombre: str, email: str) -> DestinatarioNotificacion:
    return DestinatarioNotificacion(estudiante_id=uuid4(), nombre=nombre, email=email)


class TestNotificarAperturaUseCase:
    async def test_envia_un_email_por_cada_destinatario_de_las_comisiones_restringidas(self):
        materia_id = uuid4()
        comision_a, comision_b = uuid4(), uuid4()
        comision_consulta = FakeComisionConsultaPort()
        destinatarios = [
            _destinatario("Ana", "ana@example.com"),
            _destinatario("Bruno", "bruno@example.com"),
            _destinatario("Caro", "caro@example.com"),
        ]
        comision_consulta.destinatarios_por_comisiones[
            tuple(sorted([comision_a, comision_b], key=str))
        ] = destinatarios
        canal_envio = FakeCanalEnvioPort()
        use_case = NotificarAperturaUseCase(comision_consulta, canal_envio)
        apertura, cierre = _fechas()

        await use_case.execute(
            uuid4(),
            materia_id,
            "Ingeniería de Software",
            "Parcial 1",
            apertura,
            cierre,
            [comision_a, comision_b],
        )

        assert len(canal_envio.enviados) == 3
        emails_enviados = {email for email, _asunto, _cuerpo in canal_envio.enviados}
        assert emails_enviados == {"ana@example.com", "bruno@example.com", "caro@example.com"}
        _email, asunto, cuerpo = canal_envio.enviados[0]
        assert "Parcial 1" in asunto
        assert "Ingeniería de Software" in cuerpo
        assert "Parcial 1" in cuerpo
        assert apertura.isoformat() in cuerpo
        assert cierre.isoformat() in cuerpo

    async def test_sin_restriccion_de_comision_envia_a_todas_las_de_la_materia(self):
        materia_id = uuid4()
        comision_a, comision_b = uuid4(), uuid4()
        comision_consulta = FakeComisionConsultaPort()
        comision_consulta.comisiones_por_materia[materia_id] = [comision_a, comision_b]
        destinatarios = [_destinatario("Ana", "ana@example.com")]
        comision_consulta.destinatarios_por_comisiones[
            tuple(sorted([comision_a, comision_b], key=str))
        ] = destinatarios
        canal_envio = FakeCanalEnvioPort()
        use_case = NotificarAperturaUseCase(comision_consulta, canal_envio)
        apertura, cierre = _fechas()

        await use_case.execute(
            uuid4(), materia_id, "Materia X", "Actividad", apertura, cierre, []
        )

        assert len(canal_envio.enviados) == 1
        assert canal_envio.enviados[0][0] == "ana@example.com"

    async def test_materia_sin_comisiones_no_envia_nada(self):
        materia_id = uuid4()
        comision_consulta = FakeComisionConsultaPort()
        canal_envio = FakeCanalEnvioPort()
        use_case = NotificarAperturaUseCase(comision_consulta, canal_envio)
        apertura, cierre = _fechas()

        await use_case.execute(
            uuid4(), materia_id, "Materia X", "Actividad", apertura, cierre, []
        )

        assert canal_envio.enviados == []

    async def test_fallo_de_envio_a_un_destinatario_no_aborta_el_resto(self):
        materia_id = uuid4()
        comision_a = uuid4()
        comision_consulta = FakeComisionConsultaPort()
        destinatarios = [
            _destinatario("Ana", "ana@example.com"),
            _destinatario("Bruno", "bruno@example.com"),
        ]
        comision_consulta.destinatarios_por_comisiones[(comision_a,)] = destinatarios
        canal_envio = FakeCanalEnvioPort()
        canal_envio.falla_para.add("ana@example.com")
        use_case = NotificarAperturaUseCase(comision_consulta, canal_envio)
        apertura, cierre = _fechas()

        await use_case.execute(
            uuid4(), materia_id, "Materia X", "Actividad", apertura, cierre, [comision_a]
        )

        assert len(canal_envio.enviados) == 1
        assert canal_envio.enviados[0][0] == "bruno@example.com"

    async def test_nunca_propaga_excepcion_aunque_fallen_todos_los_destinatarios(self):
        materia_id = uuid4()
        comision_a = uuid4()
        comision_consulta = FakeComisionConsultaPort()
        destinatarios = [_destinatario("Ana", "ana@example.com")]
        comision_consulta.destinatarios_por_comisiones[(comision_a,)] = destinatarios
        canal_envio = FakeCanalEnvioPort()
        canal_envio.falla_para.add("ana@example.com")
        use_case = NotificarAperturaUseCase(comision_consulta, canal_envio)
        apertura, cierre = _fechas()

        await use_case.execute(
            uuid4(), materia_id, "Materia X", "Actividad", apertura, cierre, [comision_a]
        )
