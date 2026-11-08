"""Link de invitación grupal por HTTP contra una base real (US-ADJ-67).

Requiere una base descartable (`DATABASE_URL` inline): `tests/integration/conftest.py` vacía las tablas.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text

from src.identidad.frameworks.db.models import InvitacionModel
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.inc9._link_grupal_comun import (
    _cliente,
    _escenario,
    _generar,
    _headers,
    _preview,
    _registrar,
    _revocar,
    _ultima,
    _vencer,
)


class TestGenerarLinkGrupal:
    """Generación y consulta del link grupal."""

    async def test_por_defecto_vence_en_una_hora(self, session):
        esc = await _escenario(session)

        respuesta = await _generar(esc)

        assert respuesta.status_code == 201
        datos = respuesta.json()
        vence = datetime.fromisoformat(datos["expira_en"])
        assert timedelta(minutes=58) < vence - datetime.now(UTC) <= timedelta(minutes=60)
        assert datos["comision_id"] == str(esc.comision_id)
        assert datos["token"]

    async def test_las_tres_duraciones_se_aceptan_y_otra_no(self, session):
        esc = await _escenario(session)

        aceptadas = [(await _generar(esc, m)).status_code for m in (15, 60, 1440)]
        rechazada = await _generar(esc, 90)

        assert aceptadas == [201, 201, 201]
        assert rechazada.status_code == 422

    async def test_un_docente_no_asignado_recibe_403_al_generar_ver_y_desactivar(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()
        ajeno = _headers(uuid.uuid4())

        async with _cliente() as client:
            generar = await client.post(
                f"/comisiones/{esc.comision_id}/invitaciones-grupales",
                json={},
                headers=ajeno,
            )
            ver = await client.get(
                f"/comisiones/{esc.comision_id}/invitaciones-grupales/ultima", headers=ajeno
            )
        desactivar = await _revocar(esc, link["id"], ajeno)

        assert (generar.status_code, ver.status_code, desactivar.status_code) == (403, 403, 403)

    async def test_un_estudiante_no_puede_generar(self, session):
        esc = await _escenario(session)
        estudiante = _headers(uuid.uuid4(), TipoPerfil.ESTUDIANTE)

        async with _cliente() as client:
            respuesta = await client.post(
                f"/comisiones/{esc.comision_id}/invitaciones-grupales", json={}, headers=estudiante
            )

        assert respuesta.status_code == 403

    async def test_una_comision_inexistente_da_404(self, session):
        esc = await _escenario(session)
        esc.comision_id = uuid.uuid4()

        assert (await _generar(esc)).status_code == 404

    async def test_ultima_sin_links_es_null_y_luego_trae_el_estado(self, session):
        esc = await _escenario(session)

        vacia = await _ultima(esc)
        link = (await _generar(esc)).json()
        vigente = (await _ultima(esc)).json()
        await _revocar(esc, link["id"])
        revocada = (await _ultima(esc)).json()

        assert vacia.status_code == 200 and vacia.json() is None
        assert vigente["estado"] == "vigente"
        assert vigente["token"] == link["token"]
        assert vigente["usos"] == 0
        assert revocada["estado"] == "revocada"
        assert revocada["token"] is None

    async def test_ultima_vencida_no_devuelve_el_token(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()
        await _vencer(session, link["id"])

        estado = (await _ultima(esc)).json()

        assert estado["estado"] == "vencida"
        assert estado["token"] is None


class TestRegistroConLinkGrupal:
    """Registro de estudiantes con un link grupal."""

    async def test_varios_estudiantes_con_el_mismo_link_y_el_contador_los_cuenta(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()

        respuestas = [await _registrar(link["token"], i) for i in range(3)]

        assert [r.status_code for r in respuestas] == [201, 201, 201]
        assert all(r.json()["comision_id"] == str(esc.comision_id) for r in respuestas)
        assert (await _ultima(esc)).json()["usos"] == 3

    async def test_veinte_registros_simultaneos_no_pierden_ninguna_cuenta_ni_ningun_uso(
        self, session
    ):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()

        respuestas = await asyncio.gather(*[_registrar(link["token"], i) for i in range(20)])

        assert [r.status_code for r in respuestas] == [201] * 20
        assert (await _ultima(esc)).json()["usos"] == 20

    async def test_una_contrasena_invalida_informa_su_codigo_y_no_cuenta_como_uso(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()

        sin_complejidad = await _registrar(link["token"], 1, "sinsimbolosninumeros")
        corta = await _registrar(link["token"], 2, "Corta#1234")

        for respuesta in (sin_complejidad, corta):
            assert respuesta.status_code == 422
            assert respuesta.json()["detail"]["codigo"] == "password_invalida"
        muy_corta = await _registrar(
            link["token"], 3, "corta"
        )  # lo frena el esquema, antes del dominio
        assert muy_corta.status_code == 422
        assert isinstance(muy_corta.json()["detail"], list)
        ultima = (await _ultima(esc)).json()
        assert ultima["usos"] == 0
        assert ultima["estado"] == "vigente"

    async def test_un_email_repetido_da_409_y_no_cuenta_como_uso(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()
        await _registrar(link["token"], 1, email="repetido@fiuner.edu.ar")

        segundo = await _registrar(link["token"], 2, email="repetido@fiuner.edu.ar")

        assert segundo.status_code == 409
        assert (await _ultima(esc)).json()["usos"] == 1

    async def test_el_mismo_email_en_paralelo_no_termina_en_un_error_de_servidor(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()

        respuestas = await asyncio.gather(
            *[_registrar(link["token"], i, email="doble@fiuner.edu.ar") for i in range(5)]
        )

        assert sorted(r.status_code for r in respuestas)[0] == 201
        assert all(r.status_code in (201, 409) for r in respuestas)
        assert (await _ultima(esc)).json()["usos"] == 1


class TestMotivosDelLink:
    """El preview y el registro informan el motivo con `detail.codigo`."""

    async def test_vencido(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()
        await _vencer(session, link["id"])

        preview = await _preview(link["token"])
        registro = await _registrar(link["token"], 1)

        for respuesta in (preview, registro):
            assert respuesta.status_code == 422
            assert respuesta.json()["detail"]["codigo"] == "invitacion_vencida"

    async def test_desactivado_conserva_a_los_ya_registrados(self, session):
        esc = await _escenario(session)
        link = (await _generar(esc)).json()
        await _registrar(link["token"], 1)
        await _registrar(link["token"], 2)

        primera = await _revocar(esc, link["id"])
        segunda = await _revocar(esc, link["id"])
        preview = await _preview(link["token"])
        registro = await _registrar(link["token"], 3)

        assert (primera.status_code, segunda.status_code) == (204, 204)
        for respuesta in (preview, registro):
            assert respuesta.status_code == 422
            assert respuesta.json()["detail"]["codigo"] == "invitacion_revocada"
        async with _cliente() as client:
            estudiantes = await client.get(
                f"/comisiones/{esc.comision_id}/estudiantes", headers=esc.headers
            )
        assert len(estudiantes.json()) == 2

    async def test_inexistente(self, session):
        preview = await _preview("token-que-no-existe")
        registro = await _registrar("token-que-no-existe", 1)

        assert preview.status_code == 404
        assert preview.json()["detail"]["codigo"] == "invitacion_invalida"
        assert registro.status_code == 422
        assert registro.json()["detail"]["codigo"] == "invitacion_invalida"

    async def test_generar_otro_link_desactiva_el_anterior(self, session):
        esc = await _escenario(session)
        primero = (await _generar(esc)).json()
        segundo = (await _generar(esc)).json()

        viejo = await _preview(primero["token"])
        nuevo = await _preview(segundo["token"])
        async with session.begin():
            vigentes = (
                (
                    await session.execute(
                        select(InvitacionModel).where(
                            InvitacionModel.comision_id == esc.comision_id,
                            InvitacionModel.grupal.is_(True),
                            InvitacionModel.revocada_en.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert viejo.json()["detail"]["codigo"] == "invitacion_revocada"
        assert nuevo.status_code == 200
        assert len(vigentes) == 1


class TestLinkIndividualSinCambios:
    """El endpoint individual se conserva: un uso y 7 días."""

    async def test_se_usa_una_sola_vez_y_responde_invitacion_usada(self, session):
        esc = await _escenario(session)
        async with _cliente() as client:
            generada = await client.post(
                f"/comisiones/{esc.comision_id}/invitaciones",
                json={"docente_id": str(esc.docente_id)},
                headers=esc.headers,
            )
        token = generada.json()["token"]

        primero = await _registrar(token, 1)
        segundo = await _registrar(token, 2)
        preview = await _preview(token)

        vence = datetime.fromisoformat(generada.json()["expira_en"])
        assert timedelta(days=6, hours=23) < vence - datetime.now(UTC) <= timedelta(days=7)
        assert primero.status_code == 201
        assert segundo.status_code == 422
        assert segundo.json()["detail"]["codigo"] == "invitacion_usada"
        assert preview.json()["detail"]["codigo"] == "invitacion_usada"


class TestMigracion:
    """Las invitaciones que ya existían quedan como individuales."""

    async def test_una_invitacion_anterior_a_la_migracion_es_individual_sin_usos(self, session):
        esc = await _escenario(session)
        invitacion_id = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO invitacion (id, comision_id, docente_id, token, generada_en, expira_en) "
                "VALUES (:id, :c, :d, :t, now(), now() + interval '7 days')"
            ),
            {
                "id": invitacion_id,
                "c": esc.comision_id,
                "d": esc.docente_id,
                "t": f"viejo-{invitacion_id}",
            },
        )
        await session.commit()

        fila = (
            await session.execute(
                select(InvitacionModel).where(InvitacionModel.id == invitacion_id)
            )
        ).scalar_one()

        assert (fila.grupal, fila.usos, fila.revocada_en) == (False, 0, None)
