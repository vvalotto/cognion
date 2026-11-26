"""Steps BDD de `US-12.2.1`: cada operación se guarda entera o no se guarda.

Cada escenario de fallo técnico fuerza un error en la segunda escritura contra la base real y llama al endpoint real.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import app
from src.banco_preguntas.frameworks.repositories.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.identidad.entities.token_recuperacion_password import TokenRecuperacionPassword
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.repositories.invitacion_repository import (
    SQLAlchemyInvitacionRepository,
)
from src.identidad.frameworks.repositories.token_recuperacion_password_repository import (
    SQLAlchemyTokenRecuperacionPasswordRepository,
)
from src.identidad.frameworks.repositories.usuario_repository import SQLAlchemyUsuarioRepository
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import unidad_de_trabajo
from tests.integration.inc6._helpers import (
    headers_de,
    headers_docente_de_comision,
    preparar_sesion,
)

scenarios("../../features/inc12/US-12.2.1-unidad-de-trabajo.feature")

PASSWORD_NUEVA = "NuevaClave#2026-ok"
PASSWORD_REGISTRO = "ClaveSegura#2026"
INTENTOS_MAXIMOS = 3


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with unidad_de_trabajo() as session:
        for tabla in (
            "token_recuperacion_password",
            "invitacion",
            "events",
            "pregunta_plantilla",
            "comision_docentes",
            "estudiante",
            "comision",
            "banco",
            "materia",
            "administrador",
            "docente",
            "usuario",
        ):
            await session.execute(text(f"DELETE FROM {tabla}"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


# ---------------------------------------------------------------- utilidades


def _email() -> str:
    return f"uow.{uuid.uuid4()}@fiuner.edu.ar"


def _falla_tecnica(monkeypatch: pytest.MonkeyPatch, clase: type, metodo: str) -> None:
    async def _falla(self, *args, **kwargs):  # noqa: ARG001
        raise RuntimeError(f"fallo técnico simulado en {clase.__name__}.{metodo}")

    monkeypatch.setattr(clase, metodo, _falla)


def _llamar(metodo: str, ruta: str, cuerpo: dict | None = None, headers: dict | None = None):
    with TestClient(app, raise_server_exceptions=False) as cliente:
        return cliente.request(metodo, ruta, json=cuerpo, headers=headers)


async def _escalar(sql: str, **parametros):
    async with unidad_de_trabajo() as session:
        return (await session.execute(text(sql), parametros)).scalar()


async def _crear_usuario(perfil: TipoPerfil) -> Usuario:
    usuario = Usuario.crear(
        "Usuario", _email(), BcryptPasswordHasher().hash("Original#2026-ok"), perfil
    )
    async with unidad_de_trabajo() as session:
        await SQLAlchemyUsuarioRepository(session).guardar(usuario)
    return usuario


async def _crear_token(usuario_id: uuid.UUID) -> TokenRecuperacionPassword:
    token = TokenRecuperacionPassword.crear(usuario_id)
    async with unidad_de_trabajo() as session:
        await SQLAlchemyTokenRecuperacionPasswordRepository(session).guardar(token)
    return token


async def _hash_de(usuario_id: uuid.UUID) -> str:
    return await _escalar("SELECT password_hash FROM usuario WHERE id = :i", i=str(usuario_id))


# ---------------------------------------------------------------- Given


@given("un administrador")
def un_administrador(context):
    context["headers"] = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)


@given("un administrador y un fallo al guardar el banco")
def administrador_y_fallo_del_banco(context, monkeypatch):
    context["headers"] = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    _falla_tecnica(monkeypatch, SQLAlchemyBancoRepository, "guardar")


@given("un administrador y un fallo al confirmar la transacción")
def administrador_y_fallo_del_commit(context):
    context["headers"] = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    context["commit_falla"] = True


@given("un usuario con un token de recuperación vigente y un fallo al marcar el token como usado")
def usuario_token_y_fallo_al_marcar(context, monkeypatch):
    usuario = run_async(_crear_usuario(TipoPerfil.DOCENTE))
    token = run_async(_crear_token(usuario.id))
    context.update(usuario=usuario, token=token, hash_anterior=run_async(_hash_de(usuario.id)))
    _falla_tecnica(monkeypatch, SQLAlchemyTokenRecuperacionPasswordRepository, "actualizar")


@given("un usuario con un token de recuperación vigente y un fallo al guardar el token nuevo")
def usuario_token_y_fallo_al_guardar_token(context, monkeypatch):
    usuario = run_async(_crear_usuario(TipoPerfil.DOCENTE))
    token = run_async(_crear_token(usuario.id))
    context.update(usuario=usuario, token=token)
    _falla_tecnica(monkeypatch, SQLAlchemyTokenRecuperacionPasswordRepository, "guardar")


@given("una invitación vigente y un fallo al consumir la invitación")
def invitacion_y_fallo_al_consumir(context, monkeypatch):
    _, comision_id = run_async(preparar_sesion())
    headers_docente = run_async(headers_docente_de_comision(comision_id))
    docente_id = run_async(
        _escalar("SELECT docente_id FROM comision_docentes WHERE comision_id = :c", c=comision_id)
    )
    respuesta = _llamar(
        "POST",
        f"/comisiones/{comision_id}/invitaciones",
        {"docente_id": str(docente_id)},
        headers_docente,
    )
    assert respuesta.status_code == 201, respuesta.text
    invitacion_id = respuesta.json()["id"]
    context["invitacion_id"] = invitacion_id
    context["token_invitacion"] = run_async(
        _escalar("SELECT token FROM invitacion WHERE id = :i", i=invitacion_id)
    )
    _falla_tecnica(monkeypatch, SQLAlchemyInvitacionRepository, "actualizar")


@given("un administrador, un usuario con un token de recuperación y un fallo al borrar al usuario")
def administrador_usuario_token_y_fallo_al_borrar(context, monkeypatch):
    context["headers"] = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    usuario = run_async(_crear_usuario(TipoPerfil.DOCENTE))
    context.update(usuario=usuario, token=run_async(_crear_token(usuario.id)))
    _falla_tecnica(monkeypatch, SQLAlchemyUsuarioRepository, "eliminar")


@given("un usuario al que le falta un intento para bloquearse")
def usuario_a_un_intento_de_bloquearse(context):
    usuario = run_async(_crear_usuario(TipoPerfil.DOCENTE))

    async def _acercar_al_bloqueo() -> None:
        async with unidad_de_trabajo() as session:
            await session.execute(
                text("UPDATE usuario SET intentos_fallidos_login = :n WHERE id = :i"),
                {"n": INTENTOS_MAXIMOS - 1, "i": str(usuario.id)},
            )

    run_async(_acercar_al_bloqueo())
    context["usuario"] = usuario


# ---------------------------------------------------------------- When


@when(parsers.parse('crea la materia "{nombre}"'))
def crea_la_materia(context, nombre):
    if context.get("commit_falla"):
        # El fallo vale solo durante el pedido: la limpieza de tablas del test también confirma.
        with pytest.MonkeyPatch.context() as parche:

            async def _commit_falla(self):  # noqa: ARG001
                raise RuntimeError("fallo técnico simulado al confirmar")

            parche.setattr(AsyncSession, "commit", _commit_falla)
            context["respuesta"] = _llamar(
                "POST", "/materias", {"nombre": nombre}, context["headers"]
            )
        return
    context["respuesta"] = _llamar("POST", "/materias", {"nombre": nombre}, context["headers"])


@when("confirma la nueva contraseña con ese token")
def confirma_la_nueva_contrasena(context):
    context["respuesta"] = _llamar(
        "POST",
        "/identidad/recuperar-password/confirmar",
        {"token": context["token"].token, "password_nueva": PASSWORD_NUEVA},
    )


@when("un estudiante se registra con esa invitación")
def estudiante_se_registra(context):
    context["email"] = _email()
    context["respuesta"] = _llamar(
        "POST",
        "/identidad/registro",
        {
            "token": context["token_invitacion"],
            "nombre": "Estudiante",
            "email": context["email"],
            "password": PASSWORD_REGISTRO,
        },
    )


@when("solicita recuperar su contraseña")
def solicita_recuperar(context):
    context["respuesta"] = _llamar(
        "POST", "/identidad/recuperar-password/solicitar", {"email": context["usuario"].email}
    )


@when("elimina la cuenta de ese usuario")
def elimina_la_cuenta(context):
    context["respuesta"] = _llamar(
        "DELETE", f"/usuarios/{context['usuario'].id}", headers=context["headers"]
    )


@when("ingresa una contraseña incorrecta")
def ingresa_contrasena_incorrecta(context):
    context["respuesta"] = _llamar(
        "POST",
        "/identidad/login",
        {"email": context["usuario"].email, "password": "ClaveIncorrecta#999"},
    )


# ---------------------------------------------------------------- Then


@then("la respuesta es un error de servidor")
def respuesta_error_de_servidor(context):
    assert context["respuesta"].status_code == 500, context["respuesta"].text


@then("la respuesta es de credenciales inválidas")
def respuesta_credenciales_invalidas(context):
    assert context["respuesta"].status_code == 401, context["respuesta"].text


@then(parsers.parse('existe la materia "{nombre}"'))
def existe_la_materia(nombre):
    assert run_async(_escalar("SELECT count(*) FROM materia WHERE nombre = :n", n=nombre)) == 1


@then(parsers.parse('no existe la materia "{nombre}"'))
def no_existe_la_materia(nombre):
    assert run_async(_escalar("SELECT count(*) FROM materia WHERE nombre = :n", n=nombre)) == 0


@then("esa materia tiene su banco")
def la_materia_tiene_banco():
    assert (
        run_async(_escalar("SELECT count(*) FROM banco b JOIN materia m ON m.id = b.materia_id"))
        == 1
    )


@then("la contraseña del usuario es la anterior")
def la_contrasena_es_la_anterior(context):
    assert run_async(_hash_de(context["usuario"].id)) == context["hash_anterior"]


@then("el token sigue sin usar")
def el_token_sigue_sin_usar(context):
    usado = run_async(
        _escalar(
            "SELECT usado_en FROM token_recuperacion_password WHERE id = :i",
            i=str(context["token"].id),
        )
    )
    assert usado is None


@then("el token anterior sigue vigente")
def el_token_anterior_sigue_vigente(context):
    usado = run_async(
        _escalar(
            "SELECT usado_en FROM token_recuperacion_password WHERE id = :i",
            i=str(context["token"].id),
        )
    )
    ahora = datetime.now(UTC)
    expira = run_async(
        _escalar(
            "SELECT expira_en FROM token_recuperacion_password WHERE id = :i",
            i=str(context["token"].id),
        )
    )
    assert usado is None and expira > ahora


@then("no existe el estudiante")
def no_existe_el_estudiante(context):
    assert (
        run_async(_escalar("SELECT count(*) FROM usuario WHERE email = :e", e=context["email"]))
        == 0
    )


@then("la invitación sigue vigente")
def la_invitacion_sigue_vigente(context):
    usada = run_async(
        _escalar("SELECT usada_en FROM invitacion WHERE id = :i", i=context["invitacion_id"])
    )
    assert usada is None


@then("el usuario existe")
def el_usuario_existe(context):
    assert (
        run_async(
            _escalar("SELECT count(*) FROM usuario WHERE id = :i", i=str(context["usuario"].id))
        )
        == 1
    )


@then("su token de recuperación existe")
def su_token_existe(context):
    assert (
        run_async(
            _escalar(
                "SELECT count(*) FROM token_recuperacion_password WHERE id = :i",
                i=str(context["token"].id),
            )
        )
        == 1
    )


@then("la cuenta queda bloqueada")
def la_cuenta_queda_bloqueada(context):
    bloqueada, bloqueada_hasta, intentos = run_async(_estado_de_bloqueo(context["usuario"].id))
    assert intentos >= INTENTOS_MAXIMOS
    assert bloqueada or bloqueada_hasta is not None


async def _estado_de_bloqueo(usuario_id: uuid.UUID):
    async with unidad_de_trabajo() as session:
        fila = (
            await session.execute(
                text(
                    "SELECT bloqueada, bloqueada_hasta, intentos_fallidos_login FROM usuario WHERE id = :i"
                ),
                {"i": str(usuario_id)},
            )
        ).one()
    return fila[0], fila[1], fila[2]
