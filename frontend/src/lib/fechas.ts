/**
 * Convierte el valor de un `<input type="datetime-local">` (`2026-10-25T14:00`, sin zona, hora de pared
 * del navegador) en un instante ISO con zona (`2026-10-25T17:00:00.000Z` en Argentina).
 *
 * El backend toma una hora sin zona como UTC (`US-ADJ-09`): enviar el valor crudo corría la actividad
 * tantas horas como diste de UTC (3 h en Argentina, hallazgo #7 de la UAT de `v0.9.0`).
 */
export function aIsoConZona(valorLocal: string): string {
  const fecha = new Date(valorLocal)
  if (Number.isNaN(fecha.getTime())) {
    throw new RangeError(`Fecha inválida: ${valorLocal}`)
  }
  return fecha.toISOString()
}
