"""Link de invitación grupal: agregado, casos de uso y traducción de errores (US-ADJ-67)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import (
    ComisionNoAutorizada,
    ComisionNoExiste,
    DuracionInvitacionInvalida,
    EmailYaRegistrado,
    InvitacionInvalida,
    InvitacionRevocada,
    InvitacionVencida,
    InvitacionYaUsada,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)
from src.identidad.entities.invitacion import EstadoInvitacion, Invitacion
from src.identidad.frameworks.api.errores_invitacion import error_http_de_invitacion
from src.identidad.use_cases.generar_invitacion_grupal import GenerarInvitacionGrupalUseCase
from src.identidad.use_cases.obtener_invitacion import ObtenerInvitacionUseCase
from src.identidad.use_cases.obtener_ultima_invitacion_grupal import (
    ObtenerUltimaInvitacionGrupalUseCase,
)
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase
from src.identidad.use_cases.revocar_invitacion_grupal import RevocarInvitacionGrupalUseCase
from tests.unit.inc1._fakes import (
    FakeComisionRepository,
    FakeInvitacionRepository,
    FakeMateriaPort,
    FakePasswordHasher,
    FakeUsuarioRepository,
)

PASSWORD = "Clave#Segura-2026"


def _ahora() -> datetime:
    return datetime.now(UTC)


async def _escenario():
    """Una comisión con su Docente asignado y los repositorios falsos."""
    comisiones = FakeComisionRepository()
    invitaciones = FakeInvitacionRepository()
    docente_id = uuid.uuid4()
    comision = Comision.crear(uuid.uuid4(), "lu 10-12", uuid.uuid4())
    comision.asignar_docente(docente_id)
    await comisiones.guardar(comision)
    return comisiones, invitaciones, comision, docente_id


class TestInvitacionGrupal:
    """El agregado `Invitacion` en su variante grupal."""

    def test_crear_grupal_vence_en_una_hora_por_defecto(self):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4())

        assert invitacion.grupal is True
        assert invitacion.usos == 0
        assert invitacion.expira_en - invitacion.generada_en == timedelta(minutes=60)

    @pytest.mark.parametrize("minutos", [15, 60, 1440])
    def test_las_duraciones_elegibles_se_aceptan(self, minutos):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4(), minutos)

        assert invitacion.expira_en - invitacion.generada_en == timedelta(minutes=minutos)

    @pytest.mark.parametrize("minutos", [0, 5, 90, 10080, -60])
    def test_otra_duracion_se_rechaza(self, minutos):
        with pytest.raises(DuracionInvitacionInvalida):
            Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4(), minutos)

    def test_la_individual_sigue_siendo_de_siete_dias_y_no_grupal(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())

        assert invitacion.grupal is False
        assert invitacion.expira_en - invitacion.generada_en == timedelta(days=7)

    def test_la_grupal_admite_varios_usos_y_sigue_vigente(self):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4())

        for _ in range(3):
            invitacion.aceptar(_ahora())

        assert invitacion.usada_en is None
        assert invitacion.usos == 0  # el contador lo suma la base, no el agregado
        assert invitacion.estado(_ahora()) is EstadoInvitacion.VIGENTE

    def test_la_individual_se_usa_una_sola_vez(self):
        invitacion = Invitacion.crear(uuid.uuid4(), uuid.uuid4())
        invitacion.aceptar(_ahora())

        assert invitacion.usos == 1
        assert invitacion.estado(_ahora()) is EstadoInvitacion.USADA
        with pytest.raises(InvitacionYaUsada):
            invitacion.aceptar(_ahora())

    def test_una_grupal_vencida_no_se_puede_usar(self):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4(), 15)
        despues = invitacion.expira_en + timedelta(seconds=1)

        assert invitacion.estado(despues) is EstadoInvitacion.VENCIDA
        with pytest.raises(InvitacionVencida):
            invitacion.aceptar(despues)

    def test_revocar_la_deja_inutilizable_y_es_idempotente(self):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4())

        assert invitacion.revocar(_ahora()) is True
        assert invitacion.revocar(_ahora()) is False
        assert invitacion.estado(_ahora()) is EstadoInvitacion.REVOCADA
        with pytest.raises(InvitacionRevocada):
            invitacion.aceptar(_ahora())

    def test_revocar_una_vencida_no_cambia_nada(self):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4(), 15)

        assert invitacion.revocar(invitacion.expira_en + timedelta(seconds=1)) is False
        assert invitacion.revocada_en is None

    def test_una_revocada_sigue_revocada_aunque_despues_venza(self):
        invitacion = Invitacion.crear_grupal(uuid.uuid4(), uuid.uuid4(), 15)
        invitacion.revocar(_ahora())

        assert invitacion.estado(invitacion.expira_en + timedelta(hours=1)) is (
            EstadoInvitacion.REVOCADA
        )


class TestGenerarInvitacionGrupal:
    """`GenerarInvitacionGrupalUseCase`."""

    async def test_genera_el_link_con_la_duracion_pedida(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()

        invitacion, evento = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id, 15
        )

        assert invitacion.grupal is True
        assert invitacion.docente_id == docente_id
        assert invitacion.expira_en - invitacion.generada_en == timedelta(minutes=15)
        assert evento.invitacion_id == invitacion.id
        assert invitaciones.invitaciones[invitacion.id] is invitacion

    async def test_un_docente_no_asignado_no_puede_generar(self):
        comisiones, invitaciones, comision, _docente_id = await _escenario()

        with pytest.raises(ComisionNoAutorizada):
            await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
                comision.id, uuid.uuid4()
            )
        assert invitaciones.invitaciones == {}

    async def test_una_comision_inexistente_se_rechaza(self):
        comisiones, invitaciones, _comision, docente_id = await _escenario()

        with pytest.raises(ComisionNoExiste):
            await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
                uuid.uuid4(), docente_id
            )

    async def test_una_duracion_invalida_no_revoca_el_link_vigente(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        caso = GenerarInvitacionGrupalUseCase(comisiones, invitaciones)
        vigente, _ = await caso.execute(comision.id, docente_id)

        with pytest.raises(DuracionInvitacionInvalida):
            await caso.execute(comision.id, docente_id, 90)

        assert vigente.estado(_ahora()) is EstadoInvitacion.VIGENTE

    async def test_generar_otro_revoca_el_anterior_y_deja_uno_solo_vigente(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        caso = GenerarInvitacionGrupalUseCase(comisiones, invitaciones)

        primero, _ = await caso.execute(comision.id, docente_id)
        segundo, _ = await caso.execute(comision.id, docente_id)

        assert primero.estado(_ahora()) is EstadoInvitacion.REVOCADA
        assert segundo.estado(_ahora()) is EstadoInvitacion.VIGENTE
        vigentes = [i for i in invitaciones.invitaciones.values() if i.es_vigente(_ahora())]
        assert vigentes == [segundo]

    async def test_no_toca_las_invitaciones_individuales(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        individual = Invitacion.crear(comision.id, docente_id)
        await invitaciones.guardar(individual)

        await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )

        assert individual.estado(_ahora()) is EstadoInvitacion.VIGENTE


class TestRevocarInvitacionGrupal:
    """`RevocarInvitacionGrupalUseCase`."""

    async def test_desactiva_el_link_vigente(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )

        evento = await RevocarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, invitacion.id, docente_id
        )

        assert evento is not None and evento.invitacion_id == invitacion.id
        assert invitacion.estado(_ahora()) is EstadoInvitacion.REVOCADA

    async def test_desactivar_dos_veces_no_falla(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )
        caso = RevocarInvitacionGrupalUseCase(comisiones, invitaciones)
        await caso.execute(comision.id, invitacion.id, docente_id)

        assert await caso.execute(comision.id, invitacion.id, docente_id) is None

    async def test_un_docente_no_asignado_no_puede_desactivar(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )

        with pytest.raises(ComisionNoAutorizada):
            await RevocarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
                comision.id, invitacion.id, uuid.uuid4()
            )
        assert invitacion.es_vigente(_ahora())

    async def test_no_desactiva_una_invitacion_individual_ni_ajena(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        individual = Invitacion.crear(comision.id, docente_id)
        await invitaciones.guardar(individual)
        caso = RevocarInvitacionGrupalUseCase(comisiones, invitaciones)

        with pytest.raises(InvitacionInvalida):
            await caso.execute(comision.id, individual.id, docente_id)
        with pytest.raises(InvitacionInvalida):
            await caso.execute(comision.id, uuid.uuid4(), docente_id)
        assert individual.es_vigente(_ahora())


class TestObtenerUltimaInvitacionGrupal:
    """`ObtenerUltimaInvitacionGrupalUseCase`."""

    async def test_sin_links_no_hay_estado(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()

        assert (
            await ObtenerUltimaInvitacionGrupalUseCase(comisiones, invitaciones).execute(
                comision.id, docente_id
            )
            is None
        )

    async def test_vigente_trae_el_token_y_los_registrados(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )
        invitacion.usos = 4

        estado = await ObtenerUltimaInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )

        assert estado is not None
        assert estado.estado is EstadoInvitacion.VIGENTE
        assert estado.token == invitacion.token
        assert estado.usos == 4

    async def test_revocada_o_vencida_no_devuelve_el_token(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )
        invitacion.revocar(_ahora())
        consulta = ObtenerUltimaInvitacionGrupalUseCase(comisiones, invitaciones)

        revocada = await consulta.execute(comision.id, docente_id)
        invitacion.revocada_en = None
        invitacion.expira_en = _ahora() - timedelta(minutes=1)
        vencida = await consulta.execute(comision.id, docente_id)

        assert revocada is not None and revocada.estado is EstadoInvitacion.REVOCADA
        assert vencida is not None and vencida.estado is EstadoInvitacion.VENCIDA
        assert revocada.token is None and vencida.token is None

    async def test_un_docente_no_asignado_no_la_ve(self):
        comisiones, invitaciones, comision, _docente_id = await _escenario()

        with pytest.raises(ComisionNoAutorizada):
            await ObtenerUltimaInvitacionGrupalUseCase(comisiones, invitaciones).execute(
                comision.id, uuid.uuid4()
            )


class TestRegistroConLinkGrupal:
    """`RegistrarEstudianteUseCase` y `ObtenerInvitacionUseCase` con links grupales."""

    async def _registrador(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        usuarios = FakeUsuarioRepository()
        hasher = FakePasswordHasher()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )
        return RegistrarEstudianteUseCase(invitaciones, usuarios, hasher), invitacion, usuarios

    async def test_varios_estudiantes_se_registran_con_el_mismo_link(self):
        registrar, invitacion, _usuarios = await self._registrador()

        for i in range(3):
            await registrar.execute(invitacion.token, f"Est {i}", f"e{i}@fiuner.edu.ar", PASSWORD)

        assert invitacion.usos == 3
        assert invitacion.usada_en is None
        assert invitacion.es_vigente(_ahora())

    async def test_un_registro_rechazado_no_cuenta_como_uso(self):
        registrar, invitacion, _usuarios = await self._registrador()
        await registrar.execute(invitacion.token, "Ana", "ana@fiuner.edu.ar", PASSWORD)

        with pytest.raises(EmailYaRegistrado):
            await registrar.execute(invitacion.token, "Otra", "ana@fiuner.edu.ar", PASSWORD)
        with pytest.raises(PasswordDemasiadoCorta):
            await registrar.execute(invitacion.token, "Beto", "beto@fiuner.edu.ar", "corta")
        with pytest.raises(PasswordSinComplejidadSuficiente):
            await registrar.execute(
                invitacion.token, "Beto", "beto@fiuner.edu.ar", "sinsimbolosninumeros"
            )

        assert invitacion.usos == 1

    async def test_un_link_revocado_no_permite_registrarse(self):
        registrar, invitacion, usuarios = await self._registrador()
        invitacion.revocar(_ahora())

        with pytest.raises(InvitacionRevocada):
            await registrar.execute(invitacion.token, "Ana", "ana@fiuner.edu.ar", PASSWORD)
        assert usuarios.usuarios == {}

    async def test_el_preview_distingue_el_link_revocado(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        invitacion, _ = await GenerarInvitacionGrupalUseCase(comisiones, invitaciones).execute(
            comision.id, docente_id
        )
        invitacion.revocar(_ahora())
        preview = ObtenerInvitacionUseCase(invitaciones, comisiones, FakeMateriaPort())

        with pytest.raises(InvitacionRevocada):
            await preview.execute(invitacion.token)

    async def test_la_individual_conserva_el_uso_unico(self):
        comisiones, invitaciones, comision, docente_id = await _escenario()
        individual = Invitacion.crear(comision.id, docente_id)
        await invitaciones.guardar(individual)
        registrar = RegistrarEstudianteUseCase(
            invitaciones, FakeUsuarioRepository(), FakePasswordHasher()
        )

        await registrar.execute(individual.token, "Ana", "ana@fiuner.edu.ar", PASSWORD)

        assert individual.usada_en is not None
        with pytest.raises(InvitacionYaUsada):
            await registrar.execute(individual.token, "Beto", "beto@fiuner.edu.ar", PASSWORD)


class TestErroresConCodigo:
    """Traducción de errores de dominio a respuestas HTTP con `codigo`."""

    @pytest.mark.parametrize(
        ("error", "status", "codigo"),
        [
            (InvitacionVencida("t"), 422, "invitacion_vencida"),
            (InvitacionRevocada("t"), 422, "invitacion_revocada"),
            (InvitacionYaUsada("t"), 422, "invitacion_usada"),
            (PasswordDemasiadoCorta(), 422, "password_invalida"),
            (PasswordSinComplejidadSuficiente(), 422, "password_invalida"),
        ],
    )
    def test_cada_error_lleva_su_codigo(self, error, status, codigo):
        respuesta = error_http_de_invitacion(error, status_invalida=404)

        assert respuesta.status_code == status
        assert respuesta.detail["codigo"] == codigo
        assert respuesta.detail["mensaje"] == str(error)

    @pytest.mark.parametrize("status_invalida", [404, 422])
    def test_el_status_de_invitacion_invalida_lo_decide_quien_llama(self, status_invalida):
        respuesta = error_http_de_invitacion(
            InvitacionInvalida("t"), status_invalida=status_invalida
        )

        assert respuesta.status_code == status_invalida
        assert respuesta.detail["codigo"] == "invitacion_invalida"
