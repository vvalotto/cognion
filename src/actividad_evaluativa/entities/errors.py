"""Errores de infraestructura del event store del BC Actividad Evaluativa.

No son errores de dominio (INV-AE-*) — esos se agregan aggregate por aggregate en
`US-3.1.2`/`US-3.1.3` en adelante. `ConcurrenciaOptimistaError` es un error del mecanismo de
persistencia (`BC-actividad-evaluativa-modelo.md` §6), no de una regla de negocio.
"""

from __future__ import annotations


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
