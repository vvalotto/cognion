"""Presenters de Identidad (`ADR-031`): entidades y resultados -> tipos de salida de la API.

Los `dataclass` de salida tienen los mismos campos que los esquemas de `frameworks/api/schemas.py`;
FastAPI los valida contra el `response_model` sin código extra. Sin Pydantic ni FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.ports.comision_query_port import EstudianteResumen
from src.identidad.entities.ports.materia_port import MateriaDTO
from src.identidad.entities.resultado_paginado_cuentas import ResultadoPaginadoCuentas
from src.identidad.entities.usuario import Estudiante, Usuario
from src.identidad.use_cases.listar_materias_del_estudiante import MateriaEstudianteResumen
from src.identidad.use_cases.obtener_invitacion import InvitacionPreview
from src.identidad.use_cases.obtener_ultima_invitacion_grupal import InvitacionGrupalEstado
from src.identidad.use_cases.registrar_estudiante_con_materia import EstudianteRegistrado
from src.shared.entities.jwt import JWT
from src.shared.entities.tipo_perfil import TipoPerfil


@dataclass(frozen=True)
class UsuarioSalida:
    """Un usuario recién creado."""

    id: UUID
    nombre: str
    email: str
    perfil: TipoPerfil


@dataclass(frozen=True)
class CuentaSalida:
    """Una cuenta del listado de gestión."""

    id: UUID
    nombre: str
    email: str
    perfil: TipoPerfil
    bloqueada: bool
    deshabilitada: bool


@dataclass(frozen=True)
class CuentasPaginadasSalida:
    """Una página de cuentas con el total que cumple los filtros."""

    cuentas: list[CuentaSalida]
    total: int


@dataclass(frozen=True)
class CuentaDetalleSalida:
    """El detalle de una cuenta."""

    id: UUID
    nombre: str
    email: str
    perfil: TipoPerfil
    bloqueada: bool
    creado_en: datetime
    comision_id: UUID | None
    deshabilitada: bool


@dataclass(frozen=True)
class ComisionSalida:
    """Una comisión."""

    id: UUID
    materia_id: UUID
    horario: str
    administrador_id: UUID
    docentes_asignados: list[UUID]
    activa: bool


@dataclass(frozen=True)
class ComisionResumenSalida:
    """Una comisión en el listado de una materia."""

    id: UUID
    horario: str
    docentes_asignados: list[UUID]
    activa: bool


@dataclass(frozen=True)
class EstudianteResumenSalida:
    """Un estudiante del roster de una comisión."""

    id: UUID
    nombre: str


@dataclass(frozen=True)
class InvitacionSalida:
    """Una invitación individual recién generada."""

    id: UUID
    comision_id: UUID
    docente_id: UUID
    expira_en: datetime
    token: str


@dataclass(frozen=True)
class InvitacionGrupalSalida:
    """Un link de invitación grupal recién generado."""

    id: UUID
    comision_id: UUID
    expira_en: datetime
    token: str


@dataclass(frozen=True)
class InvitacionGrupalEstadoSalida:
    """El estado del último link grupal de una comisión."""

    id: UUID
    estado: str
    token: str | None
    generada_en: datetime
    expira_en: datetime
    usos: int


@dataclass(frozen=True)
class InvitacionPreviewSalida:
    """La vista previa pública de una invitación vigente."""

    materia: str
    horario: str


@dataclass(frozen=True)
class RegistroSalida:
    """Un Estudiante recién registrado por invitación."""

    id: UUID
    nombre: str
    email: str
    comision_id: UUID
    materia: str


@dataclass(frozen=True)
class AutoregistroSalida:
    """Un usuario recién autoregistrado."""

    id: UUID
    nombre: str
    email: str
    tipo_perfil: str


@dataclass(frozen=True)
class MateriaAutoregistroSalida:
    """Una materia ofrecida en el autoregistro."""

    id: UUID
    nombre: str


@dataclass(frozen=True)
class ComisionAutoregistroSalida:
    """Una comisión ofrecida en el autoregistro."""

    id: UUID
    horario: str


@dataclass(frozen=True, kw_only=True)
class LoginSalida:
    """El resultado de iniciar sesión."""

    access_token: str
    token_type: str = "bearer"
    rol: TipoPerfil
    expira_en: datetime


@dataclass(frozen=True)
class MateriaEstudianteSalida:
    """Una materia de la comisión del Estudiante."""

    id: UUID
    nombre: str


def presentar_usuario(usuario: Usuario) -> UsuarioSalida:
    """Arma la salida de un usuario recién creado."""
    return UsuarioSalida(
        id=usuario.id, nombre=usuario.nombre, email=usuario.email, perfil=usuario.tipo_perfil
    )


def presentar_cuentas_paginadas(resultado: ResultadoPaginadoCuentas) -> CuentasPaginadasSalida:
    """Arma una página de cuentas."""
    return CuentasPaginadasSalida(
        cuentas=[
            CuentaSalida(
                id=u.id,
                nombre=u.nombre,
                email=u.email,
                perfil=u.tipo_perfil,
                bloqueada=u.bloqueada,
                deshabilitada=u.deshabilitada,
            )
            for u in resultado.cuentas
        ],
        total=resultado.total,
    )


def presentar_cuenta_detalle(usuario: Usuario) -> CuentaDetalleSalida:
    """Arma el detalle de una cuenta; `comision_id` solo existe para los Estudiantes."""
    comision_id = usuario.perfil.comision_id if isinstance(usuario.perfil, Estudiante) else None
    return CuentaDetalleSalida(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        perfil=usuario.tipo_perfil,
        bloqueada=usuario.bloqueada,
        creado_en=usuario.creado_en,
        comision_id=comision_id,
        deshabilitada=usuario.deshabilitada,
    )


def presentar_comision(comision: Comision) -> ComisionSalida:
    """Arma la salida de una comisión."""
    return ComisionSalida(
        id=comision.id,
        materia_id=comision.materia_id,
        horario=comision.horario,
        administrador_id=comision.administrador_id,
        docentes_asignados=comision.docentes_asignados,
        activa=comision.activa,
    )


def presentar_comisiones_resumen(comisiones: list[Comision]) -> list[ComisionResumenSalida]:
    """Arma el listado de comisiones de una materia."""
    return [
        ComisionResumenSalida(
            id=c.id, horario=c.horario, docentes_asignados=c.docentes_asignados, activa=c.activa
        )
        for c in comisiones
    ]


def presentar_estudiantes(estudiantes: list[EstudianteResumen]) -> list[EstudianteResumenSalida]:
    """Arma el roster de una comisión."""
    return [EstudianteResumenSalida(id=e.id, nombre=e.nombre) for e in estudiantes]


def presentar_invitacion(invitacion: Invitacion) -> InvitacionSalida:
    """Arma la salida de una invitación individual."""
    return InvitacionSalida(
        id=invitacion.id,
        comision_id=invitacion.comision_id,
        docente_id=invitacion.docente_id,
        expira_en=invitacion.expira_en,
        token=invitacion.token,
    )


def presentar_invitacion_grupal(invitacion: Invitacion) -> InvitacionGrupalSalida:
    """Arma la salida de un link de invitación grupal."""
    return InvitacionGrupalSalida(
        id=invitacion.id,
        comision_id=invitacion.comision_id,
        expira_en=invitacion.expira_en,
        token=invitacion.token,
    )


def presentar_invitacion_grupal_estado(
    estado: InvitacionGrupalEstado,
) -> InvitacionGrupalEstadoSalida:
    """Arma el estado del último link grupal."""
    return InvitacionGrupalEstadoSalida(
        id=estado.id,
        estado=estado.estado.value,
        token=estado.token,
        generada_en=estado.generada_en,
        expira_en=estado.expira_en,
        usos=estado.usos,
    )


def presentar_invitacion_preview(preview: InvitacionPreview) -> InvitacionPreviewSalida:
    """Arma la vista previa pública de una invitación."""
    return InvitacionPreviewSalida(materia=preview.materia, horario=preview.horario)


def presentar_registro(registrado: EstudianteRegistrado) -> RegistroSalida:
    """Arma la salida del registro de un Estudiante."""
    usuario = registrado.usuario
    return RegistroSalida(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        comision_id=registrado.comision_id,
        materia=registrado.materia_nombre,
    )


def presentar_autoregistro(usuario: Usuario) -> AutoregistroSalida:
    """Arma la salida del autoregistro de un usuario."""
    return AutoregistroSalida(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        tipo_perfil=usuario.tipo_perfil.value,
    )


def presentar_materias_autoregistro(materias: list[MateriaDTO]) -> list[MateriaAutoregistroSalida]:
    """Arma las materias ofrecidas en el autoregistro."""
    return [MateriaAutoregistroSalida(id=m.id, nombre=m.nombre) for m in materias]


def presentar_comisiones_autoregistro(
    comisiones: list[Comision],
) -> list[ComisionAutoregistroSalida]:
    """Arma las comisiones ofrecidas en el autoregistro."""
    return [ComisionAutoregistroSalida(id=c.id, horario=c.horario) for c in comisiones]


def presentar_login(jwt: JWT) -> LoginSalida:
    """Arma el resultado de iniciar sesión."""
    return LoginSalida(access_token=jwt.token, rol=jwt.rol, expira_en=jwt.expira_en)


def presentar_materias_estudiante(
    materias: list[MateriaEstudianteResumen],
) -> list[MateriaEstudianteSalida]:
    """Arma las materias del Estudiante."""
    return [MateriaEstudianteSalida(id=m.id, nombre=m.nombre) for m in materias]
