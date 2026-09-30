"""Servicio compartido de autorización por Comisión/Materia (`US-ADJ-57`)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.errors import ComisionNoAutorizada, MateriaNoAutorizada
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort


class VerificarAutorizacionComisionService:
    """Encapsula `ComisionConsultaPort` tras un único dependiente.

    Introducido para bajar el CBO de varios Use Case de este BC (`CerrarActividadUseCase`,
    `CrearActividadPeriodoAbiertoUseCase`, `CerrarPreguntaActualUseCase`,
    `FinalizarSesionEnVivoUseCase`, `IniciarSesionEnVivoUseCase` — todos 11-13/10 en el
    pre-push gate) — mismo criterio ya aplicado en Banco de Preguntas
    (`VerificarAutorizacionMateriaService`, `US-ADJ-57`).
    """

    def __init__(self, comision_consulta: ComisionConsultaPort) -> None:
        """Recibe el puerto de consulta de Comisión."""
        self._comision_consulta = comision_consulta

    async def verificar_materia(self, docente_id: UUID | None, materia_id: UUID) -> None:
        """No-op si `docente_id` es `None` (Administrador, sin filtro).

        Levanta `MateriaNoAutorizada` si el Docente no tiene ninguna Comisión asignada en
        `materia_id`.
        """
        if docente_id is None:
            return
        if not await self._comision_consulta.esta_asignado_a_materia(docente_id, materia_id):
            raise MateriaNoAutorizada(materia_id)

    async def verificar_comision(self, docente_id: UUID | None, comision_id: UUID) -> None:
        """No-op si `docente_id` es `None` (Administrador, sin filtro).

        Levanta `ComisionNoAutorizada` si el Docente no está asignado a `comision_id`.
        """
        if docente_id is None:
            return
        if not await self._comision_consulta.esta_asignado_a_comision(docente_id, comision_id):
            raise ComisionNoAutorizada(comision_id)
