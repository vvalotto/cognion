"""Armado compartido del mensaje `pregunta_presentada` (`US-6.1.4`, `US-6.2.6`)."""

from __future__ import annotations

from typing import Any

from src.actividad_evaluativa.entities.eventos_en_vivo import (
    SesionEnVivoIniciada,
    SiguientePreguntaPresentada,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import ContenidoPregunta

EventoPreguntaPresentada = SesionEnVivoIniciada | SiguientePreguntaPresentada


def tipo_de_pregunta(contenido: ContenidoPregunta) -> str:
    """Deriva el tipo de `opciones`: `None` = Verdadero/Falso (ver `ContenidoPregunta`)."""
    return "verdadero_falso" if contenido.opciones is None else "opcion_multiple"


def payload_pregunta_presentada(evento: EventoPreguntaPresentada) -> dict[str, Any]:
    """Arma el payload persistido de la pregunta tal como se presentó (sin opciones)."""
    return {
        "sesion_id": str(evento.sesion_id),
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "pregunta": {
            "pregunta_id": str(evento.pregunta_id),
            "enunciado": evento.enunciado,
            "tipo": evento.tipo,
        },
        "ocurrido_en": evento.ocurrido_en.isoformat(),
    }


def mensaje_pregunta_presentada(evento: EventoPreguntaPresentada) -> dict[str, Any]:
    """Arma el mensaje de broadcast: solo el enunciado de la pregunta actual, sin opciones (§16)."""
    return {
        "tipo": "pregunta_presentada",
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "pregunta": {
            "pregunta_id": str(evento.pregunta_id),
            "enunciado": evento.enunciado,
            "tipo": evento.tipo,
        },
    }
