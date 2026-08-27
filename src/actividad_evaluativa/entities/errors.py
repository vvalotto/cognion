"""Errores de infraestructura y de dominio del BC Actividad Evaluativa.

`ConcurrenciaOptimistaError` es un error del mecanismo de persistencia
(`BC-actividad-evaluativa-modelo.md` §6). Los demás son errores de dominio (INV-AE-*),
agregados aggregate por aggregate desde `US-3.1.2` en adelante.
"""

from __future__ import annotations

from datetime import datetime


class ConcurrenciaOptimistaError(Exception):
    """El `sequence_number` esperado no coincide con el último persistido del stream.

    Protege contra un doble `append` sobre el mismo stream (ej. un reintento de red del
    estudiante que reenvía el mismo comando) — ninguno de los eventos de la invocación en
    conflicto se persiste.
    """

    def __init__(
        self,
        aggregate_type: str,
        aggregate_id: object,
        expected_sequence_number: int,
        actual_sequence_number: int,
    ) -> None:
        """Guarda el stream y los números en conflicto, y arma el mensaje de la excepción."""
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.expected_sequence_number = expected_sequence_number
        self.actual_sequence_number = actual_sequence_number
        super().__init__(
            f"Concurrencia optimista: el stream ({aggregate_type}, {aggregate_id}) esperaba "
            f"sequence_number={expected_sequence_number} pero el último persistido es "
            f"{actual_sequence_number}."
        )


class MateriaNoExiste(Exception):
    """Se referenció un `materia_id` que no corresponde a ninguna `Materia` existente."""

    def __init__(self, materia_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.materia_id = materia_id
        super().__init__(f"La materia '{materia_id}' no existe.")


class PreguntasInsuficientes(Exception):
    """`cantidad_preguntas` excede las `PreguntaPlantilla` activas de la materia (INV-AE-01)."""

    def __init__(self, cantidad_solicitada: int, cantidad_disponible: int) -> None:
        """Guarda las cantidades en conflicto y arma el mensaje de la excepción."""
        self.cantidad_solicitada = cantidad_solicitada
        self.cantidad_disponible = cantidad_disponible
        super().__init__(
            f"Se solicitaron {cantidad_solicitada} preguntas pero la materia solo tiene "
            f"{cantidad_disponible} preguntas activas."
        )


class PeriodoInvalido(Exception):
    """`fecha_apertura` no es anterior a `fecha_cierre` (INV-AE-02)."""

    def __init__(self, fecha_apertura: datetime, fecha_cierre: datetime) -> None:
        """Guarda las fechas en conflicto y arma el mensaje de la excepción."""
        self.fecha_apertura = fecha_apertura
        self.fecha_cierre = fecha_cierre
        super().__init__(
            f"La fecha de apertura ({fecha_apertura}) debe ser anterior a la fecha de cierre "
            f"({fecha_cierre})."
        )


class CantidadIntentosInvalida(Exception):
    """`cantidad_intentos_permitidos` es menor a 1 (INV-AE-03)."""

    def __init__(self, cantidad_intentos_permitidos: int) -> None:
        """Guarda la cantidad inválida y arma el mensaje de la excepción."""
        self.cantidad_intentos_permitidos = cantidad_intentos_permitidos
        super().__init__(
            f"La cantidad de intentos permitidos debe ser al menos 1, se recibió "
            f"{cantidad_intentos_permitidos}."
        )


class ActividadNoExiste(Exception):
    """Se referenció un `actividad_id` sin `ActividadEvaluativaPeriodoAbierto` en su stream."""

    def __init__(self, actividad_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.actividad_id = actividad_id
        super().__init__(f"La actividad '{actividad_id}' no existe.")


class EstudianteNoExiste(Exception):
    """`estudiante_id` no corresponde a ningún `Usuario` con rol Estudiante en BC Identidad."""

    def __init__(self, estudiante_id: object) -> None:
        """Guarda el id inválido y arma el mensaje de la excepción."""
        self.estudiante_id = estudiante_id
        super().__init__(f"El estudiante '{estudiante_id}' no existe.")


class FueraDePeriodo(Exception):
    """`ahora` no está dentro de la ventana vigente de la actividad, o está cerrada manualmente."""

    def __init__(self, actividad_id: object, ahora: datetime) -> None:
        """Guarda el id de la actividad y el instante rechazado, arma el mensaje."""
        self.actividad_id = actividad_id
        self.ahora = ahora
        super().__init__(
            f"La actividad '{actividad_id}' no admite iniciar una evaluación en este momento "
            f"({ahora})."
        )


class EvaluacionNoExiste(Exception):
    """`evaluacion_id` no corresponde a ninguna `Evaluacion` existente del estudiante."""

    def __init__(self, evaluacion_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.evaluacion_id = evaluacion_id
        super().__init__(f"La evaluación '{evaluacion_id}' no existe.")


class PreguntaNoAsignada(Exception):
    """`pregunta_id` no pertenece al set `preguntas_asignadas` de la `Evaluacion` (INV-AE-07)."""

    def __init__(self, evaluacion_id: object, pregunta_id: object) -> None:
        """Guarda los ids en conflicto y arma el mensaje de la excepción."""
        self.evaluacion_id = evaluacion_id
        self.pregunta_id = pregunta_id
        super().__init__(
            f"La pregunta '{pregunta_id}' no pertenece al set asignado de la evaluación "
            f"'{evaluacion_id}'."
        )


class IntentosAgotados(Exception):
    """Se superó `cantidad_intentos_permitidos` para `pregunta_id` (INV-AE-08)."""

    def __init__(self, pregunta_id: object, cantidad_intentos_permitidos: int) -> None:
        """Guarda la pregunta y el tope en conflicto, arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        self.cantidad_intentos_permitidos = cantidad_intentos_permitidos
        super().__init__(
            f"Se agotaron los {cantidad_intentos_permitidos} intentos permitidos para la "
            f"pregunta '{pregunta_id}'."
        )


class EvaluacionSuspendida(Exception):
    """`RegistrarRespuesta` requiere `Evaluacion` `EnCurso` — está `Suspendida` (INV-AE-12)."""

    def __init__(self, evaluacion_id: object) -> None:
        """Guarda el id de la evaluación y arma el mensaje de la excepción."""
        self.evaluacion_id = evaluacion_id
        super().__init__(
            f"La evaluación '{evaluacion_id}' está suspendida — hay que reanudarla primero."
        )


class EvaluacionYaFinalizada(Exception):
    """`RegistrarRespuesta` requiere `Evaluacion` `EnCurso` — está `Finalizada` (INV-AE-12)."""

    def __init__(self, evaluacion_id: object) -> None:
        """Guarda el id de la evaluación y arma el mensaje de la excepción."""
        self.evaluacion_id = evaluacion_id
        super().__init__(f"La evaluación '{evaluacion_id}' ya está finalizada.")


class EvaluacionYaSuspendida(Exception):
    """`SuspenderEvaluacion` requiere `Evaluacion` `EnCurso` — ya está `Suspendida` (INV-AE-12)."""

    def __init__(self, evaluacion_id: object) -> None:
        """Guarda el id de la evaluación y arma el mensaje de la excepción."""
        self.evaluacion_id = evaluacion_id
        super().__init__(f"La evaluación '{evaluacion_id}' ya está suspendida.")


class EvaluacionNoSuspendida(Exception):
    """`ReanudarEvaluacion` requiere `Evaluacion` `Suspendida` — está `EnCurso` (INV-AE-11)."""

    def __init__(self, evaluacion_id: object) -> None:
        """Guarda el id de la evaluación y arma el mensaje de la excepción."""
        self.evaluacion_id = evaluacion_id
        super().__init__(
            f"La evaluación '{evaluacion_id}' no está suspendida — no hay nada que reanudar."
        )
