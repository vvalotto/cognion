"""Controller de la API del BC Analytics — desempeño individual del Estudiante.

`US-4.1.2`, `US-4.2.1`, `US-ADJ-45`. Separado de `AnalyticsInformesController`
(`analytics_informes_controller.py`, `US-ADJ-46`) — mismo criterio de separación por
responsabilidad ya aplicado en Incremento 2 (`BancosController`/`PreguntasController`,
`CuentasController`/`UsuariosController`) para no repetir el CRITICAL de CBO que salió al
mezclar demasiados Use Case en un solo controller.
"""

from __future__ import annotations

from uuid import UUID

from src.analytics.entities.errors import EstudianteNoExiste
from src.analytics.entities.ports.estudiante_consulta_port import EstudianteConsultaPort
from src.analytics.interface_adapters.presenters.analytics_presenter import (
    DesempenoEstudianteSalida,
    EvolucionTemporalPuntoSalida,
    presentar_desempeno_estudiante,
    presentar_evolucion_estudiante,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import ObtenerDesempenoEstudianteUseCase
from src.analytics.use_cases.obtener_evolucion_temporal_estudiante import (
    ObtenerEvolucionTemporalEstudianteUseCase,
)


class AnalyticsController:
    """Adapta requests HTTP de consulta de desempeño individual al Use Case correspondiente."""

    def __init__(
        self,
        obtener_desempeno_estudiante: ObtenerDesempenoEstudianteUseCase,
        obtener_evolucion_temporal_estudiante: ObtenerEvolucionTemporalEstudianteUseCase,
        estudiante_consulta: EstudianteConsultaPort,
    ) -> None:
        """Recibe los Use Case de desempeño y evolución individuales y el puerto de Estudiantes."""
        self._obtener_desempeno_estudiante = obtener_desempeno_estudiante
        self._obtener_evolucion_temporal_estudiante = obtener_evolucion_temporal_estudiante
        self._estudiante_consulta = estudiante_consulta

    async def obtener_mi_desempeno(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> DesempenoEstudianteSalida:
        """Presenta el desempeño del propio Estudiante.

        Sin `docente_id` — el propio Estudiante no tiene restricción de pertenencia
        (`US-ADJ-57`).
        """
        desempeno = await self._obtener_desempeno_estudiante.execute(estudiante_id, materia_id)
        return presentar_desempeno_estudiante(desempeno)

    async def obtener_desempeno_de_estudiante(
        self, estudiante_id: UUID, materia_id: UUID, docente_id: UUID
    ) -> DesempenoEstudianteSalida:
        """Desempeño de un Estudiante elegido por el Docente (`US-4.2.1`, RF-16).

        `estudiante_id` viene del path, así que se valida su existencia (`EstudianteNoExiste`)
        antes de calcular; `docente_id` habilita la verificación de pertenencia (`US-ADJ-57`).
        """
        await self._exigir_estudiante(estudiante_id)
        desempeno = await self._obtener_desempeno_estudiante.execute(
            estudiante_id, materia_id, docente_id
        )
        return presentar_desempeno_estudiante(desempeno)

    async def obtener_evolucion_temporal_estudiante(
        self, estudiante_id: UUID, materia_id: UUID, docente_id: UUID
    ) -> list[EvolucionTemporalPuntoSalida]:
        """Evolución temporal individual de un estudiante (`US-ADJ-45`, RF-21)."""
        await self._exigir_estudiante(estudiante_id)
        puntos = await self._obtener_evolucion_temporal_estudiante.execute(
            estudiante_id, materia_id, docente_id
        )
        return presentar_evolucion_estudiante(puntos)

    async def _exigir_estudiante(self, estudiante_id: UUID) -> None:
        """Levanta `EstudianteNoExiste` si `estudiante_id` no es un Estudiante existente."""
        if not await self._estudiante_consulta.existe(estudiante_id):
            raise EstudianteNoExiste(estudiante_id)
