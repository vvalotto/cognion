"""Router de infraestructura de tiempo real de sesiones en vivo (`US-6.1.1`).

Arrancó con el canal de broadcast por WebSocket; `US-6.1.2` agrega `POST /sesiones-en-vivo`
(crear) y `US-6.1.3`/`US-6.1.4` agregan acá el resto de los endpoints HTTP (unirse, iniciar).
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ComisionNoExiste,
    EstudianteNoExiste,
    OpcionesNoMostradasTodavia,
    OpcionesYaMostradas,
    ParticipacionNoExiste,
    PreguntaNoActual,
    PreguntasInsuficientes,
    PreguntaYaCerrada,
    RespuestaYaRegistrada,
    SesionNoEnCurso,
    SesionNoExiste,
    SesionYaFinalizada,
    SesionYaIniciada,
    TiempoAgotado,
    TiempoLimiteInvalido,
)
from src.actividad_evaluativa.frameworks.api.schemas import (
    CrearSesionEnVivoRequest,
    ParticipacionEnVivoResponse,
    ResponderEnVivoRequest,
    RespuestaEnVivoResponse,
    SesionEnVivoResponse,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    get_conduccion_en_vivo_controller,
    get_connection_manager,
    get_current_user,
    get_jwt_issuer,
    get_participaciones_en_vivo_controller,
    get_sesiones_en_vivo_controller,
    require_docente,
    require_estudiante,
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
from src.shared.entities.errors import JWTExpirado, JWTInvalido
from src.shared.entities.jwt import JWTPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sesiones-en-vivo", tags=["actividad_evaluativa_en_vivo"])


def _a_sesion_response(sesion: ActividadEvaluativaEnVivo) -> SesionEnVivoResponse:
    """Arma el `SesionEnVivoResponse` — compartido por crear e iniciar."""
    return SesionEnVivoResponse(
        id=sesion.id,
        comision_id=sesion.comision_id,
        materia_id=sesion.materia_id,
        unidad_tematica=sesion.unidad_tematica,
        tema=sesion.tema,
        cantidad_preguntas=len(sesion.preguntas),
        tiempo_limite_por_pregunta_segundos=sesion.tiempo_limite_por_pregunta_segundos,
        estado=sesion.estado.value,
        pregunta_actual_indice=sesion.pregunta_actual_indice,
    )


@router.post(
    "",
    response_model=SesionEnVivoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_docente)],
)
async def crear_sesion_en_vivo(
    body: CrearSesionEnVivoRequest,
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> SesionEnVivoResponse:
    """Crea una sesión en vivo para una Comisión; responde 404/422 ante los rechazos de dominio."""
    try:
        sesion = await controller.crear(
            body.comision_id,
            body.cantidad_preguntas,
            body.tiempo_limite_por_pregunta_segundos,
            body.unidad_tematica,
            body.tema,
        )
    except ComisionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (PreguntasInsuficientes, TiempoLimiteInvalido) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_sesion_response(sesion)


@router.post(
    "/{sesion_id}/iniciar",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def iniciar_sesion_en_vivo(
    sesion_id: UUID,
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> SesionEnVivoResponse:
    """Inicia la sesión (`EnEspera` → `EnCurso`) y presenta el enunciado; 404/422 si se rechaza."""
    try:
        sesion = await controller.iniciar(sesion_id)
    except SesionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SesionYaIniciada as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_sesion_response(sesion)


@router.post(
    "/{sesion_id}/mostrar-opciones",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def mostrar_opciones_en_vivo(
    sesion_id: UUID,
    controller: ConduccionEnVivoController = Depends(get_conduccion_en_vivo_controller),
) -> SesionEnVivoResponse:
    """Revela las opciones de la pregunta actual; 404/422 si se rechaza."""
    try:
        sesion = await controller.mostrar_opciones(sesion_id)
    except SesionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (SesionNoEnCurso, OpcionesYaMostradas) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_sesion_response(sesion)


@router.post(
    "/{sesion_id}/cerrar-pregunta",
    response_model=SesionEnVivoResponse,
    dependencies=[Depends(require_docente)],
)
async def cerrar_pregunta_en_vivo(
    sesion_id: UUID,
    controller: ConduccionEnVivoController = Depends(get_conduccion_en_vivo_controller),
) -> SesionEnVivoResponse:
    """Cierra la pregunta actual y transmite el resultado; 404/422 si se rechaza."""
    try:
        sesion = await controller.cerrar_pregunta(sesion_id)
    except SesionNoExiste as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (SesionNoEnCurso, OpcionesNoMostradasTodavia, PreguntaYaCerrada) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return _a_sesion_response(sesion)


@router.post(
    "/{sesion_id}/unirse",
    response_model=ParticipacionEnVivoResponse,
    dependencies=[Depends(require_estudiante)],
)
async def unirse_a_sesion_en_vivo(
    sesion_id: UUID,
    usuario: JWTPayload = Depends(get_current_user),
    controller: SesionesEnVivoController = Depends(get_sesiones_en_vivo_controller),
) -> ParticipacionEnVivoResponse:
    """Une al Estudiante autenticado a la sesión (idempotente, 200); 404/422 si se rechaza."""
    try:
        participacion = await controller.unirse(sesion_id, usuario.usuario_id)
    except (SesionNoExiste, EstudianteNoExiste) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SesionYaFinalizada as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return ParticipacionEnVivoResponse(
        sesion_id=participacion.sesion_id,
        estudiante_id=participacion.estudiante_id,
        unido_en=participacion.unido_en,
    )


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
) -> RespuestaEnVivoResponse:
    """Registra la respuesta del Estudiante y devuelve su feedback; 404/422 si se rechaza."""
    try:
        resultado = await controller.responder(
            sesion_id, usuario.usuario_id, body.pregunta_id, body.contenido
        )
    except (SesionNoExiste, ParticipacionNoExiste) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        SesionNoEnCurso,
        PreguntaNoActual,
        OpcionesNoMostradasTodavia,
        PreguntaYaCerrada,
        TiempoAgotado,
        RespuestaYaRegistrada,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc

    return RespuestaEnVivoResponse(
        es_correcta=resultado.es_correcta,
        puntaje=resultado.puntaje,
        puntaje_acumulado=resultado.puntaje_acumulado,
    )


@router.websocket("/{sesion_id}/canal")
async def canal_sesion_en_vivo(
    websocket: WebSocket, sesion_id: UUID, token: str | None = None
) -> None:
    """Suscribe al cliente al canal de broadcast de `sesion_id`, autenticado por JWT.

    El JWT viaja como query param (`?token=...`) — la API nativa `WebSocket` del navegador no
    permite fijar el header `Authorization` en el handshake (`US-6.1.1`). Se rechaza la
    conexión con el código `1008` (política violada) si el token falta, es inválido o expiró —
    sin verificación de rol adicional: Docente y Estudiante comparten el mismo canal de lectura
    (`BC-actividad-evaluativa-modelo.md` §16).
    """
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        get_jwt_issuer().verificar(token)
    except (JWTInvalido, JWTExpirado):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    connection_manager = get_connection_manager()
    await connection_manager.conectar(sesion_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.desconectar(sesion_id, websocket)
