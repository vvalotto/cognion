"""Puertos de los read models `ranking_por_sesion` y `distribucion_por_pregunta` (`US-6.2.3`).

Sostienen el ranking y el histograma de la sesión en vivo (`BC-actividad-evaluativa-modelo.md`
§15). Se actualizan de forma incremental con cada respuesta, no se calculan al cerrar la
pregunta: el RNF de rendimiento (≤ 100 ms, `RNF_v1.md`) no admite una agregación en ese momento.

**Contrato de atomicidad (evento + proyección):** las operaciones de escritura NO hacen
`commit`. El Use Case las ejecuta primero y luego llama a `EventStorePort.append`, cuyo `commit`
confirma ambas cosas juntas; si el `append` falla por concurrencia, el Use Case llama a
`descartar_pendientes` para que la proyección no quede confirmada sin su evento.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ParticipanteEnRanking:
    """Una fila del ranking: posición (1, 2, 3…, calculada al leer), participante y puntaje."""

    posicion: int
    estudiante_id: UUID
    puntaje_acumulado: int


@dataclass(frozen=True)
class OpcionDistribuida:
    """Cantidad de respuestas de una opción de una pregunta (solo opciones con respuestas)."""

    opcion: str
    cantidad: int


class ProyeccionesEnVivoPort(ABC):
    """Escritura de los read models de una sesión en vivo — sin `commit` (ver módulo)."""

    @abstractmethod
    async def inicializar_participante(self, sesion_id: UUID, estudiante_id: UUID) -> None:
        """Deja al participante en el ranking con 0 puntos; no hace nada si ya tiene fila."""

    @abstractmethod
    async def registrar_respuesta(
        self,
        sesion_id: UUID,
        estudiante_id: UUID,
        pregunta_id: UUID,
        opcion: str,
        puntaje: int,
    ) -> None:
        """Suma `puntaje` al acumulado del participante e incrementa en 1 la opción elegida.

        Crea la fila del participante si faltara. `opcion` es `str(opcion_indice)` para opción
        múltiple y `"verdadero"`/`"falso"` para Verdadero/Falso. Ambos incrementos son atómicos
        en la base: 60 respuestas simultáneas a la misma opción no pierden ninguna.
        """

    @abstractmethod
    async def descartar_pendientes(self) -> None:
        """Descarta lo escrito y todavía no confirmado (rollback de la unidad de trabajo)."""


class ProyeccionesEnVivoQueryPort(ABC):
    """Consulta de solo lectura de los read models de una sesión en vivo."""

    @abstractmethod
    async def ranking(self, sesion_id: UUID) -> list[ParticipanteEnRanking]:
        """Devuelve el ranking ordenado: mayor puntaje primero.

        Desempate por `ultima_actualizacion` ascendente (quien llegó antes a ese puntaje) y
        luego por `estudiante_id`, para que el orden sea determinístico.
        """

    @abstractmethod
    async def distribucion(self, sesion_id: UUID, pregunta_id: UUID) -> list[OpcionDistribuida]:
        """Devuelve la cantidad de respuestas por opción, solo de las opciones con respuestas."""

    @abstractmethod
    async def cantidad_respuestas(self, sesion_id: UUID, pregunta_id: UUID) -> int:
        """Devuelve el total de respuestas de la pregunta (suma de la distribución)."""
