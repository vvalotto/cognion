"""Presenters de Identidad (`US-12.2.4`, `ADR-031`): cada `presentar_*` arma su salida sin FastAPI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import EstadoInvitacion, Invitacion
from src.identidad.entities.ports.comision_query_port import EstudianteResumen
from src.identidad.entities.ports.materia_port import MateriaDTO
from src.identidad.entities.resultado_paginado_cuentas import ResultadoPaginadoCuentas
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    AutoregistroSalida,
    ComisionAutoregistroSalida,
    ComisionResumenSalida,
    ComisionSalida,
    EstudianteResumenSalida,
    InvitacionGrupalEstadoSalida,
    InvitacionPreviewSalida,
    LoginSalida,
    MateriaAutoregistroSalida,
    MateriaEstudianteSalida,
    UsuarioSalida,
    presentar_autoregistro,
    presentar_comision,
    presentar_comisiones_autoregistro,
    presentar_comisiones_resumen,
    presentar_cuenta_detalle,
    presentar_cuentas_paginadas,
    presentar_estudiantes,
    presentar_invitacion,
    presentar_invitacion_grupal,
    presentar_invitacion_grupal_estado,
    presentar_invitacion_preview,
    presentar_login,
    presentar_materias_autoregistro,
    presentar_materias_estudiante,
    presentar_registro,
    presentar_usuario,
)
from src.identidad.use_cases.listar_materias_del_estudiante import MateriaEstudianteResumen
from src.identidad.use_cases.obtener_invitacion import InvitacionPreview
from src.identidad.use_cases.obtener_ultima_invitacion_grupal import InvitacionGrupalEstado
from src.identidad.use_cases.registrar_estudiante_con_materia import EstudianteRegistrado
from src.shared.entities.jwt import JWT
from src.shared.entities.tipo_perfil import TipoPerfil

AHORA = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)


def test_presenta_un_usuario_creado_y_el_autoregistro() -> None:
    usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)

    assert presentar_usuario(usuario) == UsuarioSalida(
        usuario.id, "Ana", "ana@fiuner.edu.ar", TipoPerfil.DOCENTE
    )
    assert presentar_autoregistro(usuario) == AutoregistroSalida(
        usuario.id, "Ana", "ana@fiuner.edu.ar", "docente"
    )


def test_el_detalle_de_cuenta_trae_la_comision_solo_si_es_estudiante() -> None:
    comision_id = uuid4()
    estudiante = Usuario.crear_estudiante("Vale", "vale@fiuner.edu.ar", "hash", comision_id)
    docente = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)

    assert presentar_cuenta_detalle(estudiante).comision_id == comision_id
    assert presentar_cuenta_detalle(docente).comision_id is None
    assert presentar_cuenta_detalle(docente).perfil is TipoPerfil.DOCENTE


def test_presenta_una_pagina_de_cuentas() -> None:
    usuario = Usuario.crear("Ana", "ana@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)

    salida = presentar_cuentas_paginadas(ResultadoPaginadoCuentas(cuentas=[usuario], total=12))

    assert salida.total == 12
    assert salida.cuentas[0].email == "ana@fiuner.edu.ar"
    assert salida.cuentas[0].bloqueada is False


def test_presenta_comisiones_y_estudiantes() -> None:
    comision = Comision.crear(uuid4(), "lu 10-12", uuid4())
    estudiante = EstudianteResumen(id=uuid4(), nombre="Vale")

    assert presentar_comision(comision) == ComisionSalida(
        comision.id,
        comision.materia_id,
        "lu 10-12",
        comision.administrador_id,
        comision.docentes_asignados,
        True,
    )
    assert presentar_comisiones_resumen([comision]) == [
        ComisionResumenSalida(comision.id, "lu 10-12", comision.docentes_asignados, True)
    ]
    assert presentar_comisiones_autoregistro([comision]) == [
        ComisionAutoregistroSalida(comision.id, "lu 10-12")
    ]
    assert presentar_estudiantes([estudiante]) == [EstudianteResumenSalida(estudiante.id, "Vale")]


def test_presenta_las_materias() -> None:
    materia_id = uuid4()

    assert presentar_materias_autoregistro([MateriaDTO(materia_id, "ISW")]) == [
        MateriaAutoregistroSalida(materia_id, "ISW")
    ]
    assert presentar_materias_estudiante([MateriaEstudianteResumen(materia_id, "ISW")]) == [
        MateriaEstudianteSalida(materia_id, "ISW")
    ]


def test_presenta_las_invitaciones() -> None:
    invitacion = Invitacion.crear(uuid4(), uuid4())
    estado = InvitacionGrupalEstado(uuid4(), EstadoInvitacion.VIGENTE, "tok", AHORA, AHORA, 3)

    individual = presentar_invitacion(invitacion)
    grupal = presentar_invitacion_grupal(invitacion)

    assert individual.docente_id == invitacion.docente_id
    assert individual.token == invitacion.token
    assert grupal.comision_id == invitacion.comision_id
    assert presentar_invitacion_grupal_estado(estado) == InvitacionGrupalEstadoSalida(
        estado.id, "vigente", "tok", AHORA, AHORA, 3
    )
    assert presentar_invitacion_preview(InvitacionPreview("ISW", "lu 10-12")) == (
        InvitacionPreviewSalida("ISW", "lu 10-12")
    )


def test_presenta_el_registro_y_el_login() -> None:
    comision_id = uuid4()
    usuario = Usuario.crear_estudiante("Vale", "vale@fiuner.edu.ar", "hash", comision_id)

    registro = presentar_registro(EstudianteRegistrado(usuario, comision_id, "ISW"))
    login = presentar_login(JWT("tok", TipoPerfil.ESTUDIANTE, AHORA))

    assert (registro.comision_id, registro.materia) == (comision_id, "ISW")
    assert login == LoginSalida(access_token="tok", rol=TipoPerfil.ESTUDIANTE, expira_en=AHORA)
    assert login.token_type == "bearer"
