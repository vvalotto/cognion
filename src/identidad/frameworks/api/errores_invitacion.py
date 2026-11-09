"""Traducción de los errores de invitación y de contraseña a respuestas HTTP con código.

El `detail` es un objeto `{"codigo", "mensaje"}` para que el frontend sepa por qué no sirve el link
sin interpretar el texto, y no confunda una contraseña rechazada con un link inválido (`US-ADJ-67`).
Los status HTTP no cambian respecto de antes.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.identidad.entities.errors import (
    InvitacionInvalida,
    InvitacionRevocada,
    InvitacionVencida,
    InvitacionYaUsada,
    PasswordDemasiadoCorta,
    PasswordSinComplejidadSuficiente,
)

_CODIGOS: dict[type[Exception], str] = {
    InvitacionInvalida: "invitacion_invalida",
    InvitacionVencida: "invitacion_vencida",
    InvitacionRevocada: "invitacion_revocada",
    InvitacionYaUsada: "invitacion_usada",
    PasswordDemasiadoCorta: "password_invalida",
    PasswordSinComplejidadSuficiente: "password_invalida",
}


def error_http_de_invitacion(exc: Exception, *, status_invalida: int) -> HTTPException:
    """Arma la respuesta HTTP con `codigo` para un error de invitación o de contraseña.

    `status_invalida` es el status de `InvitacionInvalida` (404 en el preview, 422 en el registro);
    el resto de los errores responden siempre 422.
    """
    codigo = _CODIGOS[type(exc)]
    codigo_http = (
        status_invalida
        if isinstance(exc, InvitacionInvalida)
        else status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    return HTTPException(status_code=codigo_http, detail={"codigo": codigo, "mensaje": str(exc)})
