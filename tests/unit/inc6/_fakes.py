"""Fakes en memoria de los puertos exclusivos del modo en vivo, para tests unitarios."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
    ParticipantesSesionQueryPort,
)
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    OpcionDistribuida,
    ParticipanteEnRanking,
    ProyeccionesEnVivoPort,
    ProyeccionesEnVivoQueryPort,
)
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import (
    SesionesEnVivoQueryPort,
    SesionEnVivoResumen,
)
from tests.unit.inc3._fakes import FakeEventStore

_ESTADO_POR_EVENTO_FAKE = {
    "SesionEnVivoIniciada": EstadoSesionEnVivo.EN_CURSO,
    "SesionEnVivoFinalizada": EstadoSesionEnVivo.FINALIZADA,
}


class FakeComisionConsultaPort(ComisionConsultaPort):
    """Consulta de comisiones en memoria — devuelve lo que se precarga en `materias`."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria (`comision_id` → `materia_id`)."""
        self.materias: dict[UUID, UUID] = {}

    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` precargado, o `None` si la comisión no fue precargada."""
        return self.materias.get(comision_id)


class FakeCanalTiempoReal(CanalTiempoRealPort):
    """Canal en vivo en memoria — registra cada mensaje publicado por sesión."""

    def __init__(self) -> None:
        """Inicializa la lista de publicaciones."""
        self.publicados: list[tuple[UUID, dict[str, Any]]] = []

    async def publicar(self, sesion_id: UUID, mensaje: dict[str, Any]) -> None:
        """Registra `(sesion_id, mensaje)` en `publicados`."""
        self.publicados.append((sesion_id, mensaje))


class FakeParticipantesSesionQueryPort(ParticipantesSesionQueryPort):
    """Read model en memoria — deriva los participantes de los eventos del `FakeEventStore`.

    Igual que el adapter real, lee los `EstudianteUnido` del event store en vez de mantener una
    proyección aparte.
    """

    def __init__(self, event_store: FakeEventStore) -> None:
        """Recibe el event store del que leer los streams de `ParticipacionEnVivo`."""
        self._event_store = event_store

    async def listar(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los participantes de `sesion_id` en orden de unión."""
        participantes = [
            ParticipanteResumen(
                estudiante_id=UUID(evento.payload["estudiante_id"]),
                unido_en=datetime.fromisoformat(evento.payload["unido_en"]),
            )
            for (aggregate_type, _), stream in self._event_store._streams.items()
            if aggregate_type == "ParticipacionEnVivo"
            for evento in stream
            if evento.event_type == "EstudianteUnido"
            and evento.payload["sesion_id"] == str(sesion_id)
        ]
        return sorted(participantes, key=lambda p: p.unido_en)


class FakeSesionesEnVivoQueryPort(SesionesEnVivoQueryPort):
    """Read model en memoria — deriva las sesiones de los eventos del `FakeEventStore`.

    Igual que el adapter real, agrupa los eventos de `ActividadEvaluativaEnVivo` por stream en
    vez de mantener una proyección aparte.
    """

    def __init__(self, event_store: FakeEventStore) -> None:
        """Recibe el event store del que leer los streams de `ActividadEvaluativaEnVivo`."""
        self._event_store = event_store

    async def listar(
        self, comision_id: UUID, estados: list[EstadoSesionEnVivo]
    ) -> list[SesionEnVivoResumen]:
        """Devuelve las sesiones de `comision_id` cuyo estado está en `estados`."""
        resumenes = []
        for (aggregate_type, aggregate_id), stream in self._event_store._streams.items():
            if aggregate_type != "ActividadEvaluativaEnVivo" or not stream:
                continue
            primero = stream[0]
            if primero.payload["comision_id"] != str(comision_id):
                continue
            estado = EstadoSesionEnVivo.EN_ESPERA
            for evento in stream:
                estado = _ESTADO_POR_EVENTO_FAKE.get(evento.event_type, estado)
            if estado not in estados:
                continue
            resumenes.append(
                SesionEnVivoResumen(
                    id=aggregate_id,
                    comision_id=comision_id,
                    materia_id=UUID(primero.payload["materia_id"]),
                    cantidad_preguntas=len(primero.payload["preguntas"]),
                    tiempo_limite_por_pregunta_segundos=primero.payload[
                        "tiempo_limite_por_pregunta_segundos"
                    ],
                    estado=estado,
                    creada_en=primero.occurred_at,
                    unidad_tematica=primero.payload.get("unidad_tematica"),
                    tema=primero.payload.get("tema"),
                )
            )
        return sorted(resumenes, key=lambda resumen: resumen.creada_en, reverse=True)


class FakeProyeccionesEnVivo(ProyeccionesEnVivoPort, ProyeccionesEnVivoQueryPort):
    """Read models en memoria — aplican de inmediato (la atomicidad real se prueba en integración)."""

    def __init__(self) -> None:
        """Inicializa el ranking, la distribución y el contador de descartes."""
        self.puntajes: dict[tuple[UUID, UUID], int] = {}
        self.conteos: dict[tuple[UUID, UUID, str], int] = {}
        self.descartes = 0

    async def inicializar_participante(self, sesion_id: UUID, estudiante_id: UUID) -> None:
        """Deja al participante con 0 puntos si todavía no tiene fila."""
        self.puntajes.setdefault((sesion_id, estudiante_id), 0)

    async def registrar_respuesta(
        self, sesion_id: UUID, estudiante_id: UUID, pregunta_id: UUID, opcion: str, puntaje: int
    ) -> None:
        """Suma el puntaje e incrementa la opción elegida."""
        clave = (sesion_id, estudiante_id)
        self.puntajes[clave] = self.puntajes.get(clave, 0) + puntaje
        clave_opcion = (sesion_id, pregunta_id, opcion)
        self.conteos[clave_opcion] = self.conteos.get(clave_opcion, 0) + 1

    async def descartar_pendientes(self) -> None:
        """Registra que se pidió descartar lo pendiente."""
        self.descartes += 1

    async def ranking(self, sesion_id: UUID) -> list[ParticipanteEnRanking]:
        """Ranking por puntaje descendente (sin desempate temporal: el fake no lo modela)."""
        filas = sorted(
            ((e, p) for (s, e), p in self.puntajes.items() if s == sesion_id),
            key=lambda fila: (-fila[1], str(fila[0])),
        )
        return [ParticipanteEnRanking(i, e, p) for i, (e, p) in enumerate(filas, start=1)]

    async def distribucion(self, sesion_id: UUID, pregunta_id: UUID) -> list[OpcionDistribuida]:
        """Cantidad por opción ordenada por opción."""
        return [
            OpcionDistribuida(opcion, cantidad)
            for (s, p, opcion), cantidad in sorted(self.conteos.items())
            if s == sesion_id and p == pregunta_id
        ]

    async def cantidad_respuestas(self, sesion_id: UUID, pregunta_id: UUID) -> int:
        """Total de respuestas de la pregunta."""
        return sum(o.cantidad for o in await self.distribucion(sesion_id, pregunta_id))
