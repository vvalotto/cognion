"""Helpers compartidos de los tests de integración de sesiones en vivo (US-6.1.3 en adelante)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def headers_de(usuario_id: uuid.UUID, rol: TipoPerfil) -> dict[str, str]:
    """Header `Authorization` con un JWT válido del rol indicado."""
    return {"Authorization": f"Bearer {PyJWTIssuer().emitir(usuario_id, rol).token}"}


async def crear_estudiante(comision_id: str) -> tuple[str, dict[str, str]]:
    """Crea un `Usuario` Estudiante real en la Comisión indicada; devuelve su id y sus headers."""
    async with SessionLocal() as session:
        estudiante = Usuario.crear_estudiante(
            "Estudiante",
            f"estudiante.{uuid.uuid4()}@fiuner.edu.ar",
            BcryptPasswordHasher().hash("x"),
            uuid.UUID(comision_id),
        )
        await SQLAlchemyUsuarioRepository(session).guardar(estudiante)
    return str(estudiante.id), headers_de(estudiante.id, TipoPerfil.ESTUDIANTE)


async def preparar_sesion(
    cantidad_preguntas: int = 10, opcion_multiple: bool = False
) -> tuple[str, str]:
    """Crea materia con preguntas, Comisión y una sesión en vivo `EnEspera` (US-6.1.2).

    Devuelve `(sesion_id, comision_id)`. Usa la API real para crear la sesión. Las preguntas son
    de Verdadero/Falso salvo que `opcion_multiple` sea `True` (opciones "A" a "D", la "B" correcta).
    """
    admin = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    docente = headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin
        )
        banco_id = creada.json()["banco_id"]
        materia_id = creada.json()["id"]
        for i in range(cantidad_preguntas):
            comun = {
                "banco_id": banco_id,
                "texto": f"Pregunta {i}",
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            }
            if opcion_multiple:
                ruta = "/preguntas/opcion-multiple"
                cuerpo = {
                    **comun,
                    "opciones": [{"texto": letra, "es_correcta": letra == "B"} for letra in "ABCD"],
                }
            else:
                ruta = "/preguntas/verdadero-falso"
                cuerpo = {**comun, "respuesta_correcta": True}
            await client.post(ruta, json=cuerpo, headers=docente)

        async with SessionLocal() as session:
            admin_usuario = Usuario.crear(
                "Admin",
                f"admin.{uuid.uuid4()}@fiuner.edu.ar",
                BcryptPasswordHasher().hash("x"),
                TipoPerfil.ADMINISTRADOR,
            )
            await SQLAlchemyUsuarioRepository(session).guardar(admin_usuario)
            comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin_usuario.id)
            await SQLAlchemyComisionRepository(session).guardar(comision)

        respuesta = await client.post(
            "/sesiones-en-vivo",
            json={
                "comision_id": str(comision.id),
                "cantidad_preguntas": min(5, cantidad_preguntas),
                "tiempo_limite_por_pregunta_segundos": 30,
            },
            headers=docente,
        )
    return respuesta.json()["id"], str(comision.id)


async def iniciar_sesion(sesion_id: str) -> None:
    """Inicia la sesión por la API real (US-6.1.4) — reemplaza la siembra de `SesionEnVivoIniciada`."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/iniciar",
            headers=headers_de(uuid.uuid4(), TipoPerfil.DOCENTE),
        )
    assert respuesta.status_code == 200, respuesta.text


async def sembrar_evento_de_sesion(sesion_id: str, tipo: str, secuencia: int) -> None:
    """Agrega un evento posterior al stream de la sesión, directo en el event store.

    `SesionEnVivoFinalizada` (Iteración 2) todavía no se emite por API — los tests de sesión
    finalizada lo siembran a mano. `SesionEnVivoIniciada` ya sale de `iniciar_sesion` (US-6.1.4).
    """
    async with SessionLocal() as session:
        await SQLAlchemyEventStore(session).append(
            "ActividadEvaluativaEnVivo",
            uuid.UUID(sesion_id),
            secuencia - 1,
            [
                EventoParaAlmacenar(
                    event_type=tipo,
                    payload={"sesion_id": sesion_id, "ocurrido_en": datetime.now(UTC).isoformat()},
                )
            ],
        )


def correr(coro):
    """`asyncio.run` — para tests sincrónicos (WebSocket) que necesitan preparar datos async."""
    return asyncio.run(coro)


async def unirse_a_sesion(sesion_id: str, headers: dict[str, str]) -> None:
    """Une al Estudiante a la sesión por la API real (US-6.1.3)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers)
    assert respuesta.status_code == 200, respuesta.text


async def mostrar_opciones(sesion_id: str) -> None:
    """Muestra las opciones de la pregunta actual por la API real (US-6.2.2)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/mostrar-opciones",
            headers=headers_de(uuid.uuid4(), TipoPerfil.DOCENTE),
        )
    assert respuesta.status_code == 200, respuesta.text


async def sembrar_opciones_mostradas_hace(sesion_id: str, segundos: float) -> None:
    """Siembra `OpcionesEnVivoMostradas` con `ocurrido_en` en el pasado (para `TiempoAgotado`).

    Reemplaza `mostrar_opciones` cuando el test necesita controlar el instante de referencia.
    """
    from datetime import timedelta

    async with SessionLocal() as session:
        store = SQLAlchemyEventStore(session)
        eventos = await store.load("ActividadEvaluativaEnVivo", uuid.UUID(sesion_id))
        pregunta = eventos[0].payload["preguntas"][0]["pregunta_id"]
        await store.append(
            "ActividadEvaluativaEnVivo",
            uuid.UUID(sesion_id),
            len(eventos),
            [
                EventoParaAlmacenar(
                    event_type="OpcionesEnVivoMostradas",
                    payload={
                        "sesion_id": sesion_id,
                        "pregunta_actual_indice": 0,
                        "pregunta_id": pregunta,
                        "opciones": None,
                        "ocurrido_en": (
                            datetime.now(UTC) - timedelta(seconds=segundos)
                        ).isoformat(),
                    },
                )
            ],
        )


async def pregunta_actual_de(sesion_id: str) -> str:
    """Devuelve el `pregunta_id` de la primera pregunta de la sesión (la actual tras iniciar)."""
    async with SessionLocal() as session:
        eventos = await SQLAlchemyEventStore(session).load(
            "ActividadEvaluativaEnVivo", uuid.UUID(sesion_id)
        )
    return eventos[0].payload["preguntas"][0]["pregunta_id"]
