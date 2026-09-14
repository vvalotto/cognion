"""Use Case de `ObtenerCompletitudPorActividadUseCase` (US-ADJ-47, RF-23)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.analytics.entities.errors import ActividadNoExiste
from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    EstudianteResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    ActividadResumen,
    EvaluacionDesempenoConsultaPort,
)

_SIN_INICIAR = "sin_iniciar"


@dataclass(frozen=True)
class CompletitudFila:
    """Estado de un estudiante del roster aplicable frente a una actividad puntual."""

    estudiante_id: UUID
    nombre: str
    estado: str


@dataclass(frozen=True)
class CompletitudResumen:
    """Conteo agregado del roster por estado, para el encabezado de la pantalla."""

    finalizadas: int
    en_curso: int
    suspendidas: int
    sin_iniciar: int


@dataclass(frozen=True)
class CompletitudPorActividad:
    """Resultado completo: detalle por estudiante más el resumen agregado."""

    detalle: list[CompletitudFila]
    resumen: CompletitudResumen


class ObtenerCompletitudPorActividadUseCase:
    """Docente consulta la completitud de una actividad puntual (RF-23)."""

    def __init__(
        self,
        evaluacion_puerto: EvaluacionDesempenoConsultaPort,
        comision_puerto: ComisionConsultaPort,
    ) -> None:
        """Recibe los dos puertos de consulta necesarios para resolver el roster y sus estados."""
        self._evaluacion_puerto = evaluacion_puerto
        self._comision_puerto = comision_puerto

    async def execute(self, actividad_id: UUID) -> CompletitudPorActividad:
        """Resuelve el roster aplicable de la actividad y el estado de cada estudiante."""
        actividad = await self._evaluacion_puerto.obtener_actividad_resumen(actividad_id)
        if actividad is None:
            raise ActividadNoExiste(actividad_id)

        roster = await _roster_aplicable(self._comision_puerto, actividad)
        estados = await self._evaluacion_puerto.listar_estados_de_actividad(
            actividad_id, [estudiante.id for estudiante in roster]
        )
        detalle = _detalle_de(roster, estados)
        return CompletitudPorActividad(detalle=detalle, resumen=_resumen_de(detalle))


async def _roster_aplicable(
    comision_puerto: ComisionConsultaPort, actividad: ActividadResumen
) -> list[EstudianteResumen]:
    """Roster de la(s) comisión(es) restringida(s), o de toda la materia si no hay restricción.

    Función de módulo — mismo criterio de simplicidad de `execute()` que el resto del BC.
    """
    comisiones_ids: set[UUID] | frozenset[UUID]
    if actividad.comisiones_ids:
        comisiones_ids = actividad.comisiones_ids
    else:
        comisiones = await comision_puerto.listar_comisiones_por_materia(actividad.materia_id)
        comisiones_ids = {comision.id for comision in comisiones}

    vistos: dict[UUID, EstudianteResumen] = {}
    for comision_id in comisiones_ids:
        for estudiante in await comision_puerto.listar_estudiantes(comision_id):
            vistos[estudiante.id] = estudiante
    return list(vistos.values())


def _detalle_de(roster: list[EstudianteResumen], estados: dict[UUID, str]) -> list[CompletitudFila]:
    """Combina el roster con el estado resuelto de cada estudiante, `sin_iniciar` por defecto."""
    return [
        CompletitudFila(
            estudiante_id=estudiante.id,
            nombre=estudiante.nombre,
            estado=estados.get(estudiante.id, _SIN_INICIAR),
        )
        for estudiante in roster
    ]


def _resumen_de(detalle: list[CompletitudFila]) -> CompletitudResumen:
    """Cuenta el detalle por estado para armar el resumen agregado."""
    return CompletitudResumen(
        finalizadas=sum(1 for fila in detalle if fila.estado == "finalizada"),
        en_curso=sum(1 for fila in detalle if fila.estado == "en_curso"),
        suspendidas=sum(1 for fila in detalle if fila.estado == "suspendida"),
        sin_iniciar=sum(1 for fila in detalle if fila.estado == _SIN_INICIAR),
    )
