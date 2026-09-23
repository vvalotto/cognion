export type ColorOpcion = "a" | "b" | "c" | "d"

export interface OpcionEnVivo {
  texto: string
  color: ColorOpcion
}

const COLORES: ColorOpcion[] = ["a", "b", "c", "d"]
const TIPO_VERDADERO_FALSO = "verdadero_falso"

/**
 * Opciones de una pregunta en vivo con su color (`--stage-color-*`): Verdadero/Falso usa `b`/`c`
 * (no rojo/verde, para no sugerir la correcta — H1); con N opciones los colores se reparten
 * `a, b, c, d` y se repiten cíclicamente (H2). Compartido entre proyección y celular.
 */
export function opcionesEnVivo(tipo: string, opciones: string[] | null): OpcionEnVivo[] {
  if (tipo === TIPO_VERDADERO_FALSO) {
    return [
      { texto: "Verdadero", color: "b" },
      { texto: "Falso", color: "c" },
    ]
  }
  return (opciones ?? []).map((texto, indice) => ({
    texto,
    color: COLORES[indice % COLORES.length],
  }))
}

/** Estilo de una caja de opción — el amarillo lleva texto oscuro para mantener el contraste. */
export function estiloOpcion(color: ColorOpcion): { background: string; color: string } {
  return {
    background: `var(--stage-color-${color})`,
    color: color === "c" ? "#2a1c00" : "#ffffff",
  }
}
