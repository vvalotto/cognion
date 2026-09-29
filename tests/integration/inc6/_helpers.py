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
from src.identidad.frameworks.db.models import comision_docentes
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def headers_de(usuario_id: uuid.UUID, rol: TipoPerfil) -> dict[str, str]:
    """Header `Authorization` con un JWT válido del rol indicado."""
    return {"Authorization": f"Bearer {PyJWTIssuer().emitir(usuario_id, rol).token}"}


async def headers_docente_de_comision(comision_id: str) -> dict[str, str]:
    """Headers del Docente realmente asignado a la Comisión indicada (`US-ADJ-57`).

    Reemplaza `headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)` (anónimo, sin Comisión) al operar
    sobre una Comisión ya existente — `POST /sesiones-en-vivo` y el resto de los endpoints de
    conducción exigen que el Docente que llama esté asignado a ella.
    """
    async with SessionLocal() as session:
        resultado = await session.execute(
            comision_docentes.select().where(
                comision_docentes.c.comision_id == uuid.UUID(comision_id)
            )
        )
        fila = resultado.first()
        assert fila is not None, f"Comisión {comision_id} sin Docente asignado"
        return headers_de(fila.docente_id, TipoPerfil.DOCENTE)


async def headers_docente_de_sesion(sesion_id: str) -> dict[str, str]:
    """Headers del Docente realmente asignado a la Comisión de la sesión (`US-ADJ-57`).

    Reemplaza `headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)` (anónimo, sin Comisión) en los
    helpers que operan sobre una sesión ya creada — los endpoints de conducción ahora exigen
    que el Docente que llama esté asignado a la Comisión de la sesión. Si `sesion_id` no tiene
    stream (caso "sesión inexistente" de varios tests), devuelve un Docente anónimo — el
    endpoint responde `SesionNoExiste` (404) antes de llegar al chequeo de pertenencia.
    """
    async with SessionLocal() as session:
        eventos = await SQLAlchemyEventStore(session).load(
            "ActividadEvaluativaEnVivo", uuid.UUID(sesion_id)
        )
        if not eventos:
            return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)
        comision_id = str(uuid.UUID(eventos[0].payload["comision_id"]))
    return await headers_docente_de_comision(comision_id)


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


async def crear_estudiantes(comision_id: str, cantidad: int) -> list[tuple[str, dict[str, str]]]:
    """Crea `cantidad` Estudiantes reales en una sola sesión de DB, hasheando la clave una vez.

    A diferencia de `crear_estudiante` (un bcrypt por llamada), sirve para los 60 participantes
    de la verificación de rendimiento sin gastar ~15 s solo en preparar los datos (US-6.2.9).
    Devuelve `[(estudiante_id, headers)]`.
    """
    password_hash = BcryptPasswordHasher().hash("x")
    estudiantes = [
        Usuario.crear_estudiante(
            f"Estudiante {i}",
            f"estudiante.{uuid.uuid4()}@fiuner.edu.ar",
            password_hash,
            uuid.UUID(comision_id),
        )
        for i in range(cantidad)
    ]
    async with SessionLocal() as session:
        repositorio = SQLAlchemyUsuarioRepository(session)
        for estudiante in estudiantes:
            await repositorio.guardar(estudiante)
    return [(str(e.id), headers_de(e.id, TipoPerfil.ESTUDIANTE)) for e in estudiantes]


async def preparar_sesion(
    cantidad_preguntas: int = 10, opcion_multiple: bool = False
) -> tuple[str, str]:
    """Crea materia con preguntas, Comisión y una sesión en vivo `EnEspera` (US-6.1.2).

    Devuelve `(sesion_id, comision_id)`. Usa la API real para crear la sesión. Las preguntas son
    de Verdadero/Falso salvo que `opcion_multiple` sea `True` (opciones "A" a "D", la "B" correcta).
    `US-ADJ-57`: cargar preguntas exige que el Docente tenga una Comisión asignada en la
    materia — la Comisión se crea y se asigna antes del loop, no después.
    """
    admin = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin
        )
        banco_id = creada.json()["banco_id"]
        materia_id = creada.json()["id"]

        async with SessionLocal() as session:
            admin_usuario = Usuario.crear(
                "Admin",
                f"admin.{uuid.uuid4()}@fiuner.edu.ar",
                BcryptPasswordHasher().hash("x"),
                TipoPerfil.ADMINISTRADOR,
            )
            await SQLAlchemyUsuarioRepository(session).guardar(admin_usuario)
            docente_usuario = Usuario.crear(
                "Docente",
                f"docente.{uuid.uuid4()}@fiuner.edu.ar",
                BcryptPasswordHasher().hash("x"),
                TipoPerfil.DOCENTE,
            )
            await SQLAlchemyUsuarioRepository(session).guardar(docente_usuario)

            comision_repo = SQLAlchemyComisionRepository(session)
            comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin_usuario.id)
            await comision_repo.guardar(comision)
            comision.asignar_docente(docente_usuario.id)
            await comision_repo.actualizar(comision)

        docente = headers_de(docente_usuario.id, TipoPerfil.DOCENTE)

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


async def asegurar_participante(sesion_id: str) -> None:
    """Une a un Estudiante nuevo **solo si** la sesión todavía no tiene ninguno (INV-AEV-11).

    Desde `US-ADJ-58` no se inicia una sesión sin participantes. Los tests que no se ocupan de los
    participantes siguen iniciando igual; los que ya unen a sus Estudiantes no cambian su conteo.
    """
    docente = await headers_docente_de_sesion(sesion_id)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        participantes = await client.get(
            f"/sesiones-en-vivo/{sesion_id}/participantes", headers=docente
        )
        assert participantes.status_code == 200, participantes.text
        if participantes.json():
            return
        estado = await client.get(f"/sesiones-en-vivo/{sesion_id}", headers=docente)
        assert estado.status_code == 200, estado.text
    _, headers = await crear_estudiante(estado.json()["comision_id"])
    await unirse_a_sesion(sesion_id, headers)


async def iniciar_sesion(sesion_id: str) -> None:
    """Inicia la sesión por la API real (US-6.1.4) — reemplaza la siembra de `SesionEnVivoIniciada`.

    Si nadie se unió todavía, une a un Estudiante antes (`asegurar_participante`, INV-AEV-11).
    """
    await asegurar_participante(sesion_id)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/iniciar",
            headers=await headers_docente_de_sesion(sesion_id),
        )
    assert respuesta.status_code == 200, respuesta.text


async def cerrar_pregunta_actual(sesion_id: str) -> None:
    """Cierra la pregunta actual por la API real (US-6.2.5); requiere las opciones ya mostradas."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/cerrar-pregunta",
            headers=await headers_docente_de_sesion(sesion_id),
        )
    assert respuesta.status_code == 200, respuesta.text


async def finalizar_sesion(sesion_id: str) -> None:
    """Finaliza la sesión por la API real (US-6.2.7) — reemplaza la siembra de `Finalizada`.

    Requiere la sesión `EnCurso` con la pregunta actual cerrada.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.post(
            f"/sesiones-en-vivo/{sesion_id}/finalizar",
            headers=await headers_docente_de_sesion(sesion_id),
        )
    assert respuesta.status_code == 200, respuesta.text


async def iniciar_y_finalizar(sesion_id: str) -> None:
    """Lleva una sesión `EnEspera` a `Finalizada`: iniciar, mostrar, cerrar y finalizar (API real)."""
    await iniciar_sesion(sesion_id)
    await mostrar_opciones(sesion_id)
    await cerrar_pregunta_actual(sesion_id)
    await finalizar_sesion(sesion_id)


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
            headers=await headers_docente_de_sesion(sesion_id),
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
