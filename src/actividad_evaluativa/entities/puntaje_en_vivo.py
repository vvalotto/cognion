"""Puntaje de una respuesta en sesión en vivo (RF-10, spike 2026-09-17).

Función de dominio pura, sin I/O: la consume `ResponderPreguntaEnVivo` (`US-6.2.4`). El puntaje
nunca lo calcula ni lo envía el cliente. `NivelPregunta` es vocabulario propio de Actividad
Evaluativa — el BC no importa los enums de `banco_preguntas`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

_PUNTAJE_BASE = 1000
_FACTOR_TIEMPO_MINIMO = 0.5


class NivelPregunta(StrEnum):
    """Nivel de dificultad o de importancia de una pregunta."""

    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


@dataclass(frozen=True)
class NivelesDePregunta:
    """Dificultad e importancia vigentes de una pregunta, resultado de `obtener_niveles`."""

    dificultad: NivelPregunta
    importancia: NivelPregunta


_FACTOR_POR_NIVEL: dict[NivelPregunta, float] = {
    NivelPregunta.BAJO: 1.0,
    NivelPregunta.MEDIO: 1.5,
    NivelPregunta.ALTO: 2.0,
}


def calcular_puntaje(
    es_correcta: bool,
    tiempo_respuesta_segundos: float,
    tiempo_limite_segundos: float,
    dificultad: NivelPregunta,
    importancia: NivelPregunta,
) -> int:
    """Calcula el puntaje de una respuesta: 0 si es incorrecta, entre 500 y 4000 si es correcta.

    `1000 × FactorTiempo × FactorDificultad × FactorImportancia`, con `FactorTiempo` lineal en
    `[0.5, 1.0]`. El tiempo se acota a `[0, tiempo_limite]`: el rechazo por `TiempoAgotado` es
    responsabilidad de `US-6.2.4` (INV-AEV-08), no de esta función. Redondea una sola vez, al
    final. `tiempo_limite <= 0` lanza `ValueError` (INV-AEV-02 ya lo impide al crear la sesión).
    """
    if tiempo_limite_segundos <= 0:
        raise ValueError("tiempo_limite_segundos debe ser mayor que 0")
    if not es_correcta:
        return 0

    tiempo = min(max(tiempo_respuesta_segundos, 0), tiempo_limite_segundos)
    factor_tiempo = _FACTOR_TIEMPO_MINIMO + 0.5 * (1 - tiempo / tiempo_limite_segundos)
    return round(
        _PUNTAJE_BASE
        * factor_tiempo
        * _FACTOR_POR_NIVEL[dificultad]
        * _FACTOR_POR_NIVEL[importancia]
    )
