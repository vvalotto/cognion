from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Comision:
    id: UUID
    materia: str
    horario: str
    administrador_id: UUID
    docentes_asignados: list[UUID] = field(default_factory=list)

    @staticmethod
    def crear(materia: str, horario: str, administrador_id: UUID) -> Comision:
        return Comision(
            id=uuid4(),
            materia=materia,
            horario=horario,
            administrador_id=administrador_id,
        )

    def asignar_docente(self, docente_id: UUID) -> None:
        if docente_id not in self.docentes_asignados:
            self.docentes_asignados.append(docente_id)
