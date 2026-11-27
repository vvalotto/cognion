"""Router de infraestructura de tiempo real de sesiones en vivo (`US-6.1.1`).

Arrancó con el canal de broadcast por WebSocket; `US-6.1.2` agrega `POST /sesiones-en-vivo`
(crear) y `US-6.1.3`/`US-6.1.4` agregan acá el resto de los endpoints HTTP (unirse, iniciar).
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.frameworks.api.schemas import (
    CrearSesionEnVivoRequest,
    EstadoSesionEnVivoResponse,
    ParticipacionEnVivoResponse,
    ParticipanteResponse,
    RankingItemResponse,
    ResponderEnVivoRequest,
    RespuestaEnVivoResponse,
    SesionEnVivoResponse,
    SesionEnVivoResumenResponse,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    autorizar_acceso_sesion,
    get_conduccion_en_vivo_controller,
    get_connection_manager,
    get_current_user,
    get_jwt_issuer,
    get_participaciones_en_vivo_controller,
    get_sesiones_en_vivo_controller,
    get_sesiones_en_vivo_listado_controller,
    get_sesiones_en_vivo_query_controller,
    puede_conectar_al_canal,
    require_docente,
    require_estudiante,
    require_estudiante_o_docente,
)
from src.actividad_evaluativa.interface_adapters.controllers.conduccion_en_vivo_controller import (
    ConduccionEnVivoController,
)
from src.actividad_evaluativa.interface_adapters.controllers.participaciones_en_vivo_controller import (
    ParticipacionesEnVivoController,
)
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_controller import (
    SesionesEnVivoController,
)
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_listado_controller import (
    SesionesEnVivoListadoController,
)
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_query_controller import (
    SesionesEnVivoQueryController,
)
from src.actividad_evaluativa.interface_adapters.presenters.sesion_en_vivo_presenter import (
    EstadoSesionEnVivoSalida,
    ParticipacionEnVivoSalida,
    ParticipanteSalida,
    RankingItemSalida,
    RespuestaEnVivoSalida,
    SesionEnVivoResumenSalida,
    SesionEnVivoSalida,
)
from src.shared.entities.errors import JWTExpirado, JWTInvalido
from src.shared.entities.jwt import JWTPayload
from src.shared.entities.tipo_perfil import TipoPerfil

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sesiones-en-vivo", tags=["actividad_evaluativa_en_vivo"])


@router.post(
    "",
    response_model=SesionEnVivoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def crear_sesion_en_vivo(
    body: CrearSesionEnVivoRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Crea una sesión en vivo para una Comisión; responde 404/422/403 ante los rechazos.

    403 si el Docente no está asignado a `comision_id` (`US-ADJ-57`).
    """
    return await controller.crear(
        body.comision_id,
        body.cantidad_preguntas,
        body.tiempo_limite_por_pregunta_segundos,
        body.unidad_tematica,
        body.tema,
        usuario.usuario_id,
    )


@router.post(
    "/{sesion_id}/iniciar",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def iniciar_sesion_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Inicia la sesión (`EnEspera` → `EnCurso`) y presenta el enunciado; 404/422/403 si se rechaza."""
    return await controller.iniciar(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/cancelar",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def cancelar_sesion_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Cancela una sesión `EnEspera` y avisa a la sala (`US-ADJ-58`); 404/422/403 si se rechaza."""
    return await controller.cancelar(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/mostrar-opciones",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def mostrar_opciones_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ConduccionEnVivoController = Depends(get_conduccion_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Revela las opciones de la pregunta actual; 404/422/403 si se rechaza."""
    return await controller.mostrar_opciones(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/cerrar-pregunta",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def cerrar_pregunta_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ConduccionEnVivoController = Depends(get_conduccion_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Cierra la pregunta actual y transmite el resultado; 404/422/403 si se rechaza."""
    return await controller.cerrar_pregunta(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/avanzar",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def avanzar_siguiente_pregunta_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ConduccionEnVivoController = Depends(get_conduccion_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Avanza a la siguiente pregunta y transmite su enunciado; 404/422/403 si se rechaza."""
    return await controller.avanzar_siguiente_pregunta(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/finalizar",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def finalizar_sesion_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ConduccionEnVivoController = Depends(get_conduccion_en_vivo_controller),
) -> SesionEnVivoSalida:
    """Finaliza la sesión y transmite el ranking final; 404/422/403 si se rechaza."""
    return await controller.finalizar_sesion(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/unirse",
    response_model=ParticipacionEnVivoResponse,
    dependencies=[Depends(require_estudiante), Depends(autorizar_acceso_sesion)],
)
async def unirse_a_sesion_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> ParticipacionEnVivoSalida:
    """Une al Estudiante de la comisión a la sesión (idempotente, 200); 403/404/422 si se rechaza."""
    return await controller.unirse(sesion_id, usuario.usuario_id)


@router.post(
    "/{sesion_id}/responder",
    response_model=RespuestaEnVivoResponse,
    dependencies=[Depends(require_estudiante)],
)
async def responder_pregunta_en_vivo(
    sesion_id: UUID,
    body: ResponderEnVivoRequest,
    usuario: JWTPayload = Depends(get_current_user),
    controller: ParticipacionesEnVivoController = Depends(get_participaciones_en_vivo_controller),
) -> RespuestaEnVivoSalida:
    """Registra la respuesta del Estudiante y devuelve su feedback; 404/422 si se rechaza."""
    return await controller.responder(
        sesion_id, usuario.usuario_id, body.pregunta_id, body.contenido
    )


@router.websocket("/{sesion_id}/canal")
async def canal_sesion_en_vivo(
    websocket: WebSocket, sesion_id: UUID, token: str | None = None
) -> None:
    """Suscribe al cliente al canal de broadcast de `sesion_id`, autenticado por JWT.

    El JWT viaja como query param (`?token=...`) — la API nativa `WebSocket` del navegador no
    permite fijar el header `Authorization` en el handshake (`US-6.1.1`). Se rechaza la
    conexión con el código `1008` (política violada) si el token falta, es inválido o expiró, y
    también si el usuario no pertenece a la comisión de la sesión (`US-12.1.1`): el docente
    asignado a ella, un estudiante de ella o un administrador. Una sesión inexistente se rechaza
    igual. Docente y Estudiante comparten el mismo canal de lectura
    (`BC-actividad-evaluativa-modelo.md` §16).
    """
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = get_jwt_issuer().verificar(token)
    except (JWTInvalido, JWTExpirado):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if not await puede_conectar_al_canal(sesion_id, payload.usuario_id, payload.rol):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    connection_manager = get_connection_manager()
    await connection_manager.conectar(sesion_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.desconectar(sesion_id, websocket)


@router.get("", response_model=list[SesionEnVivoResumenResponse])
async def listar_sesiones_en_vivo(
    comision_id: UUID | None = None,
    estado: list[EstadoSesionEnVivo] = Query(
        default=[EstadoSesionEnVivo.EN_ESPERA, EstadoSesionEnVivo.EN_CURSO]
    ),
    usuario: JWTPayload = Depends(require_estudiante_o_docente),
    controller: SesionesEnVivoListadoController = Depends(get_sesiones_en_vivo_listado_controller),
) -> list[SesionEnVivoResumenSalida]:
    """Lista las sesiones en vivo de una Comisión (la del Estudiante, o la que indique el Docente).

    422 si el Docente no indica `comision_id`; 403 si el Estudiante pide la de otro.
    """
    return await controller.listar_sesiones(usuario.usuario_id, usuario.rol, comision_id, estado)


@router.get(
    "/{sesion_id}",
    response_model=EstadoSesionEnVivoResponse,
    dependencies=[Depends(require_estudiante_o_docente), Depends(autorizar_acceso_sesion)],
)
async def obtener_estado_sesion_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(require_estudiante_o_docente),
    controller: SesionesEnVivoQueryController = Depends(get_sesiones_en_vivo_query_controller),
) -> EstadoSesionEnVivoSalida:
    """Devuelve el estado de la sesión para reconectarse; al Estudiante suma su avance propio."""
    estudiante_id = usuario.usuario_id if usuario.rol == TipoPerfil.ESTUDIANTE else None
    return await controller.obtener_estado(sesion_id, estudiante_id)


@router.get(
    "/{sesion_id}/participantes",
    response_model=list[ParticipanteResponse],
    dependencies=[Depends(require_docente)],
)
async def listar_participantes_de_sesion(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: SesionesEnVivoQueryController = Depends(get_sesiones_en_vivo_query_controller),
) -> list[ParticipanteSalida]:
    """Lista los Estudiantes unidos, en orden de unión, para la sala de espera del Docente."""
    return await controller.listar_participantes(sesion_id, usuario.usuario_id)


@router.get(
    "/{sesion_id}/ranking",
    response_model=list[RankingItemResponse],
    dependencies=[Depends(require_estudiante_o_docente), Depends(autorizar_acceso_sesion)],
)
async def obtener_ranking_de_sesion(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(require_estudiante_o_docente),
    controller: SesionesEnVivoQueryController = Depends(get_sesiones_en_vivo_query_controller),
) -> list[RankingItemSalida]:
    """Devuelve el ranking; el Estudiante solo lo ve con la sesión finalizada (403 antes)."""
    return await controller.obtener_ranking(sesion_id, usuario.rol == TipoPerfil.ESTUDIANTE)
