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

export interface FilaHistograma extends OpcionEnVivo {
  cantidad: number
  esCorrecta: boolean
}

interface RespuestaCorrectaEnVivo {
  contenido: Record<string, unknown>
  opciones: string[] | null
}

interface OpcionDistribuida {
  opcion: string
  cantidad: number
}

/**
 * Una fila por **cada** opción de la pregunta, con su cantidad y si es la correcta. El servidor solo
 * manda las opciones elegidas al menos una vez (clave = índice como texto, o `verdadero`/`falso`): las
 * que faltan se completan en 0.
 */
export function filasHistograma(
  tipo: string,
  respuestaCorrecta: RespuestaCorrectaEnVivo | null,
  distribucion: OpcionDistribuida[],
): FilaHistograma[] {
  const cantidades = new Map(distribucion.map((fila) => [fila.opcion, fila.cantidad]))
  const contenido = respuestaCorrecta?.contenido ?? {}

  if (tipo === TIPO_VERDADERO_FALSO) {
    return opcionesEnVivo(tipo, null).map((opcion, indice) => {
      const valor = indice === 0
      const clave = valor ? "verdadero" : "falso"
      return { ...opcion, cantidad: cantidades.get(clave) ?? 0, esCorrecta: contenido.valor === valor }
    })
  }

  return opcionesEnVivo(tipo, respuestaCorrecta?.opciones ?? null).map((opcion, indice) => ({
    ...opcion,
    cantidad: cantidades.get(String(indice)) ?? 0,
    esCorrecta: contenido.opcion_indice === indice,
  }))
}
