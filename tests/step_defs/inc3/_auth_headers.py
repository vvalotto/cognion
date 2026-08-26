"""Headers de autorización para los steps BDD de Actividad Evaluativa (`US-3.1.2`)."""

from __future__ import annotations

import uuid

from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def docente_headers() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}
