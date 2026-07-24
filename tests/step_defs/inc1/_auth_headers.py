"""Headers de autorización para los steps BDD de Identidad (`US-1.1.5`).

Los tokens se emiten directo con `PyJWTIssuer`, sin pasar por `/identidad/login` — igual que
en un despliegue real, el primer `Administrador` no puede autenticarse contra la API para
crear su propia cuenta (huevo-y-gallina, ver nota de `US-1.1.0` en `docs/plans/inc1/inc1-candidatas.md`).
"""

from __future__ import annotations

import uuid

from src.identidad.entities.usuario import TipoPerfil
from src.identidad.frameworks.security.jwt_pyjwt import PyJWTIssuer


def admin_headers() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def docente_headers() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}
