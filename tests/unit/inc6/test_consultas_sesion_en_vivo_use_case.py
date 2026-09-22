"""Tests unitarios de los casos de uso de consulta de la sesión en vivo (US-6.2.8)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import RankingNoDisponible, SesionNoExiste
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import (
    ContenidoPregunta,
    DetalleCorreccionPregunta,
)
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_query_controller import (
    SesionesEnVivoQueryController,
)
from src.actividad_evaluativa.use_cases.cerrar_pregunta_actual import CerrarPreguntaActualUseCase
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.finalizar_sesion_en_vivo import (
    FinalizarSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import IniciarSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.listar_participantes import ListarParticipantesUseCase
from src.actividad_evaluativa.use_cases.mostrar_opciones_en_vivo import (
    MostrarOpcionesEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.obtener_estado_sesion import ObtenerEstadoSesionUseCase
from src.actividad_evaluativa.use_cases.obtener_ranking import ObtenerRankingUseCase
from src.actividad_evaluativa.use_cases.unirse_a_sesion_en_vivo import (
    AGGREGATE_TYPE_PARTICIPACION,
    UnirseASesionEnVivoUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)
from tests.unit.inc6._fakes import (
    FakeCanalTiempoReal,
    FakeComisionConsultaPort,
    FakeParticipantesSesionQueryPort,
    FakeProyeccionesEnVivo,
)

OPCIONES = ["A", "B", "C", "D"]


class _Escenario:
    """Sesión armada con los use cases reales y los use cases de consulta a probar."""

    async def armar(self, iniciada: bool = False):
        comision_id, materia_id = uuid4(), uuid4()
        comision_consulta = FakeComisionConsultaPort()
        comision_consulta.materias[comision_id] = materia_id
        self.pregunta_consulta = FakePreguntaConsultaPort()
        self.pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(5)]
        self.event_store = FakeEventStore()
        self.sesion = await CrearSesionEnVivoUseCase(
            comision_consulta, self.pregunta_consulta, self.event_store
        ).execute(comision_id, 3, 45)
        for i, asignada in enumerate(self.sesion.preguntas):
            self.pregunta_consulta.contenidos[asignada.pregunta_id] = ContenidoPregunta(
                texto=f"Enunciado {i}", opciones=OPCIONES
            )
            self.pregunta_consulta.detalles[asignada.pregunta_id] = DetalleCorreccionPregunta(
                texto=f"Detalle {i}", contenido_correcto={"opcion_indice": 2}, opciones=OPCIONES
            )
        self.estudiantes = FakeEstudianteConsultaPort()
        self.canal = FakeCanalTiempoReal()
        self.proyecciones = FakeProyeccionesEnVivo()
        self.participantes = FakeParticipantesSesionQueryPort(self.event_store)
        if iniciada:
            await IniciarSesionEnVivoUseCase(
                self.event_store, self.pregunta_consulta, self.canal
            ).execute(self.sesion.id)
        self.estado = ObtenerEstadoSesionUseCase(self.event_store, self.pregunta_consulta)
        self.listar = ListarParticipantesUseCase(
            self.event_store, self.participantes, self.estudiantes
        )
        self.ranking = ObtenerRankingUseCase(self.event_store, self.proyecciones, self.estudiantes)
        return self

    async def unir(self) -> object:
        estudiante_id = uuid4()
        self.estudiantes.estudiantes.add(estudiante_id)
        await UnirseASesionEnVivoUseCase(
            self.estudiantes,
            self.event_store,
            self.participantes,
            self.canal,
            self.proyecciones,
        ).execute(self.sesion.id, estudiante_id)
        return estudiante_id

    async def mostrar(self) -> None:
        await MostrarOpcionesEnVivoUseCase(
            self.event_store, self.pregunta_consulta, self.canal
        ).execute(self.sesion.id)

    async def cerrar(self) -> None:
        await CerrarPreguntaActualUseCase(
            self.event_store,
            self.proyecciones,
            self.pregunta_consulta,
            self.canal,
            self.estudiantes,
        ).execute(self.sesion.id)

    async def finalizar(self) -> None:
        await FinalizarSesionEnVivoUseCase(
            self.event_store, self.proyecciones, self.canal, self.estudiantes
        ).execute(self.sesion.id)

    async def registrar_respuesta(self, estudiante_id, pregunta_id, puntaje: int) -> None:
        """Siembra una `RespuestaEnVivoRegistrada` en el stream del Estudiante."""
        from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo

        pid = ParticipacionEnVivo.id_para(self.sesion.id, estudiante_id)
        existentes = await self.event_store.load(AGGREGATE_TYPE_PARTICIPACION, pid)
        await self.event_store.append(
            AGGREGATE_TYPE_PARTICIPACION,
            pid,
            len(existentes),
            [
                EventoParaAlmacenar(
                    event_type="RespuestaEnVivoRegistrada",
                    payload={
                        "pregunta_id": str(pregunta_id),
                        "contenido": {"opcion_indice": 2},
                        "es_correcta": True,
                        "tiempo_respuesta_segundos": 3.0,
                        "puntaje": puntaje,
                    },
                )
            ],
        )


async def _escenario(iniciada: bool = False) -> _Escenario:
    return await _Escenario().armar(iniciada)


class TestObtenerEstado:
    async def test_sesion_en_espera_sin_pregunta_actual(self):
        e = await _escenario()

        estado = await e.estado.execute(e.sesion.id)

        assert estado.sesion.estado.value == "EnEspera"
        assert estado.pregunta_actual is None
        assert estado.ya_respondio is None and estado.puntaje_acumulado is None

    async def test_solo_enunciado_sin_opciones_ni_correcta(self):
        e = await _escenario(iniciada=True)

        estado = await e.estado.execute(e.sesion.id)

        pregunta = estado.pregunta_actual
        assert pregunta is not None and pregunta.enunciado.startswith("Enunciado")
        assert pregunta.opciones is None and pregunta.respuesta_correcta is None

    async def test_con_opciones_mostradas_expone_opciones_y_referencia_de_tiempo(self):
        e = await _escenario(iniciada=True)
        await e.mostrar()

        estado = await e.estado.execute(e.sesion.id)

        assert estado.pregunta_actual.opciones == OPCIONES
        assert estado.pregunta_actual.respuesta_correcta is None
        assert estado.opciones_mostradas_en is not None
        assert estado.sesion.tiempo_limite_por_pregunta_segundos == 45

    async def test_con_la_pregunta_cerrada_expone_la_correcta(self):
        e = await _escenario(iniciada=True)
        await e.mostrar()
        await e.cerrar()

        estado = await e.estado.execute(e.sesion.id)

        assert estado.pregunta_actual.respuesta_correcta["contenido"] == {"opcion_indice": 2}

    async def test_verdadero_falso_no_tiene_opciones(self):
        e = await _escenario(iniciada=True)
        actual = e.sesion.preguntas[0].pregunta_id
        e.pregunta_consulta.contenidos[actual] = ContenidoPregunta(texto="VF", opciones=None)
        e.sesion = (await e.estado.execute(e.sesion.id)).sesion
        await e.mostrar()

        estado = await e.estado.execute(e.sesion.id)

        assert estado.pregunta_actual.tipo == "verdadero_falso"
        assert estado.pregunta_actual.opciones is None

    async def test_estudiante_ve_su_avance(self):
        e = await _escenario(iniciada=True)
        estudiante_id = await e.unir()
        await e.registrar_respuesta(estudiante_id, e.sesion.preguntas[0].pregunta_id, 1200)

        estado = await e.estado.execute(e.sesion.id, estudiante_id)

        assert estado.ya_respondio is True
        assert estado.puntaje_acumulado == 1200

    async def test_estudiante_que_no_respondio_la_actual(self):
        e = await _escenario(iniciada=True)
        estudiante_id = await e.unir()
        await e.registrar_respuesta(estudiante_id, uuid4(), 800)

        estado = await e.estado.execute(e.sesion.id, estudiante_id)

        assert estado.ya_respondio is False
        assert estado.puntaje_acumulado == 800

    async def test_estudiante_sin_participacion_recibe_ceros(self):
        e = await _escenario(iniciada=True)

        estado = await e.estado.execute(e.sesion.id, uuid4())

        assert estado.ya_respondio is False and estado.puntaje_acumulado == 0

    async def test_estudiante_sin_pregunta_actual_no_respondio(self):
        e = await _escenario()
        estudiante_id = await e.unir()

        estado = await e.estado.execute(e.sesion.id, estudiante_id)

        assert estado.ya_respondio is False and estado.puntaje_acumulado == 0

    async def test_no_escribe_eventos(self):
        e = await _escenario(iniciada=True)
        antes = len(await e.event_store.load("ActividadEvaluativaEnVivo", e.sesion.id))

        await e.estado.execute(e.sesion.id)

        assert len(await e.event_store.load("ActividadEvaluativaEnVivo", e.sesion.id)) == antes

    async def test_sesion_inexistente(self):
        e = await _escenario()

        with pytest.raises(SesionNoExiste):
            await e.estado.execute(uuid4())


class TestListarParticipantes:
    async def test_lista_en_orden_de_union(self):
        e = await _escenario()
        ids = [await e.unir() for _ in range(3)]

        participantes = await e.listar.execute(e.sesion.id)

        assert [p.estudiante_id for p in participantes] == ids

    async def test_sesion_inexistente(self):
        e = await _escenario()

        with pytest.raises(SesionNoExiste):
            await e.listar.execute(uuid4())

    async def test_trae_el_nombre_resuelto_de_cada_participante(self):
        e = await _escenario()
        estudiante_id = await e.unir()
        e.estudiantes.nombres_por_estudiante[estudiante_id] = "Juan Pérez"

        participantes = await e.listar.execute(e.sesion.id)

        assert participantes[0].nombre == "Juan Pérez"

    async def test_participante_sin_nombre_resoluble(self):
        e = await _escenario()
        estudiante_id = await e.unir()

        participantes = await e.listar.execute(e.sesion.id)

        assert participantes[0].nombre == "Estudiante sin nombre"


class TestObtenerRanking:
    async def test_docente_lo_ve_en_cualquier_momento(self):
        e = await _escenario(iniciada=True)
        ana = uuid4()
        await e.proyecciones.registrar_respuesta(e.sesion.id, ana, uuid4(), "A", 500)

        ranking = await e.ranking.execute(e.sesion.id, es_estudiante=False)

        assert [(r.posicion, r.estudiante_id, r.puntaje_acumulado) for r in ranking] == [
            (1, ana, 500)
        ]

    async def test_trae_el_nombre_resuelto_del_estudiante(self):
        e = await _escenario(iniciada=True)
        ana = uuid4()
        await e.proyecciones.registrar_respuesta(e.sesion.id, ana, uuid4(), "A", 500)
        e.estudiantes.nombres_por_estudiante[ana] = "Ana Torres"

        ranking = await e.ranking.execute(e.sesion.id, es_estudiante=False)

        assert ranking[0].nombre == "Ana Torres"

    async def test_estudiante_no_lo_ve_antes_de_finalizar(self):
        e = await _escenario(iniciada=True)

        with pytest.raises(RankingNoDisponible):
            await e.ranking.execute(e.sesion.id, es_estudiante=True)

    async def test_estudiante_lo_ve_al_finalizar(self):
        e = await _escenario(iniciada=True)
        await e.mostrar()
        await e.cerrar()
        await e.finalizar()
        ana = uuid4()
        await e.proyecciones.registrar_respuesta(e.sesion.id, ana, uuid4(), "A", 500)

        ranking = await e.ranking.execute(e.sesion.id, es_estudiante=True)

        assert len(ranking) == 1

    async def test_sesion_inexistente(self):
        e = await _escenario()

        with pytest.raises(SesionNoExiste):
            await e.ranking.execute(uuid4(), es_estudiante=False)


class TestControllerDeConsultas:
    async def test_delega_en_los_tres_use_cases(self):
        e = await _escenario(iniciada=True)
        estudiante_id = await e.unir()
        controller = SesionesEnVivoQueryController(e.estado, e.listar, e.ranking)

        estado = await controller.obtener_estado(e.sesion.id, estudiante_id)
        participantes = await controller.listar_participantes(e.sesion.id)
        ranking = await controller.obtener_ranking(e.sesion.id, es_estudiante=False)

        assert estado.ya_respondio is False
        assert [p.estudiante_id for p in participantes] == [estudiante_id]
        assert len(ranking) == 1
