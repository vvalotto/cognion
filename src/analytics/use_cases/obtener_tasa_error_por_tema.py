"""Caso de uso: tasa de error por unidad/tema de una materia, o de una comisión (`US-4.2.4`)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.analytics.entities.errors import ComisionNoPerteneceAMateria
from src.analytics.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
)
from src.analytics.entities.ports.pregunta_metadato_consulta_port import (
    PreguntaMetadatoConsultaPort,
)


@dataclass(frozen=True)
class TasaErrorTema:
    """Agregado de error de un `(unidad_tematica, tema)` sobre las respuestas consultadas."""

    unidad_tematica: str
    tema: str
    cantidad_respuestas: int
    cantidad_incorrectas: int
    tasa_error: float


class ObtenerTasaErrorPorTemaUseCase:
    """Agrega respuestas vigentes por tema, acotando opcionalmente a una comisión (RF-17).

    Compone `EvaluacionDesempenoConsultaPort.listar_respuestas_vigentes_de_materia`
    (`US-4.1.1`/`US-4.2.4`), `ComisionConsultaPort.listar_estudiantes` (`US-4.2.2`, solo si
    `comision_id` viene informado) y `PreguntaMetadatoConsultaPort.obtener_metadatos`
    (`US-4.2.3`) — sin puerto ni evento propio, Analytics no tiene aggregate.
    """

    def __init__(
        self,
        evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort,
        comision_consulta: ComisionConsultaPort,
        pregunta_metadato_consulta: PreguntaMetadatoConsultaPort,
    ) -> None:
        """Recibe los 3 puertos de consulta que compone el agregado."""
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta
        self._comision_consulta = comision_consulta
        self._pregunta_metadato_consulta = pregunta_metadato_consulta

    async def execute(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[TasaErrorTema]:
        """Devuelve la tasa de error por tema, ordenada descendente (temas más problemáticos primero).

        `comision_id` que no pertenece a `materia_id` → `raise ComisionNoPerteneceAMateria`
        (el router lo mapea a 422). Sin `comision_id`, agrega toda la materia.
        """
        estudiante_ids = await self._resolver_estudiante_ids(materia_id, comision_id)
        respuestas = await self._evaluacion_desempeno_consulta.listar_respuestas_vigentes_de_materia(
            materia_id, estudiante_ids
        )
        if not respuestas:
            return []

        metadatos = await self._pregunta_metadato_consulta.obtener_metadatos(
            list({respuesta.pregunta_id for respuesta in respuestas})
        )

        acumulado: dict[tuple[str, str], list[int]] = {}
        for respuesta in respuestas:
            metadato = metadatos.get(respuesta.pregunta_id)
            if metadato is None:
                continue
            clave = (metadato.unidad_tematica, metadato.tema)
            contador = acumulado.setdefault(clave, [0, 0])
            contador[0] += 1
            if not respuesta.es_correcta:
                contador[1] += 1

        tasas = [
            TasaErrorTema(
                unidad_tematica=unidad_tematica,
                tema=tema,
                cantidad_respuestas=cantidad_respuestas,
                cantidad_incorrectas=cantidad_incorrectas,
                tasa_error=cantidad_incorrectas / cantidad_respuestas,
            )
            for (unidad_tematica, tema), (
                cantidad_respuestas,
                cantidad_incorrectas,
            ) in acumulado.items()
        ]
        return sorted(tasas, key=lambda tasa: tasa.tasa_error, reverse=True)

    async def _resolver_estudiante_ids(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[UUID] | None:
        """`None` si no se acota a comisión; lista de estudiantes de la comisión si sí."""
        if comision_id is None:
            return None
        comisiones = await self._comision_consulta.listar_comisiones_por_materia(materia_id)
        if comision_id not in {comision.id for comision in comisiones}:
            raise ComisionNoPerteneceAMateria(comision_id, materia_id)
        estudiantes = await self._comision_consulta.listar_estudiantes(comision_id)
        return [estudiante.id for estudiante in estudiantes]
