/**
 * `true` si una actividad ya cerrada tiene una `fechaCierre` todavía por venir: se cerró a mano,
 * antes de lo programado (`US-ADJ-61`, hallazgo H-1 de la UAT 7-ADJ). El cierre manual solo marca
 * la actividad como cerrada y no mueve `fecha_cierre`, así que esa fecha no dice cuándo cerró.
 */
export function cerroAntesDeLoPrevisto(fechaCierreIso: string, ahora: Date = new Date()): boolean {
  return new Date(fechaCierreIso).getTime() > ahora.getTime()
}
