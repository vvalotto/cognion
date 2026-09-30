import type { KeyboardEvent } from "react"

const TECLAS_NO_ENTERAS = new Set(["-", "+", "e", "E", ".", ","])

/**
 * `onKeyDown` de los `<input type="number">` de cantidades: impide tipear signos, exponentes y
 * decimales (revisión manual 2026-09-26: no se pueden ingresar valores negativos). Lo pegado lo
 * frena igual la validación al enviar (`esEnteroPositivo`).
 */
export function soloEnterosPositivos(event: KeyboardEvent<HTMLInputElement>) {
  if (TECLAS_NO_ENTERAS.has(event.key)) event.preventDefault()
}

/** ¿Es un entero ≥ 1? (`Number("")` es 0, así que un campo vacío tampoco pasa). */
export function esEnteroPositivo(valor: number): boolean {
  return Number.isInteger(valor) && valor >= 1
}
