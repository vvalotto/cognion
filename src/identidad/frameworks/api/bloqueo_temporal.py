"""Respuesta HTTP compartida del bloqueo temporal de cuenta (INV-ID-21)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status

from src.identidad.entities.errors import CuentaBloqueadaTemporalmenteError


def respuesta_bloqueo_temporal(exc: CuentaBloqueadaTemporalmenteError) -> HTTPException:
    """Arma el 403 con `detail` estructurado y los segundos que faltan para reintentar."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "codigo": "cuenta_bloqueada_temporal",
            "mensaje": str(exc),
            "reintentar_en_segundos": exc.segundos_restantes(datetime.now(UTC)),
        },
    )
