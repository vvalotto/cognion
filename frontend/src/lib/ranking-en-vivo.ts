export const PUESTOS_RANKING = 3

interface ConPosicion {
  posicion: number
}

/** Top 3 del ranking (decisión de Víctor, 2026-09-21): tantos puestos como haya, hasta 3. */
export function top3<T extends ConPosicion>(ranking: T[]): T[] {
  return [...ranking].sort((a, b) => a.posicion - b.posicion).slice(0, PUESTOS_RANKING)
}
