import type { PreguntaResponse } from "@/lib/banco-preguntas-api"

/**
 * Regla común Unidad temática → Tema (`wireframes-banco-preguntas.md` §2.3.1, hallazgo #6 de la UAT de
 * `v0.9.0`). Las opciones salen de las preguntas activas del banco: el Tema solo ofrece los temas de la
 * unidad elegida, y todos los del banco si no hay unidad elegida.
 */

type ConUnidadYTema = Pick<PreguntaResponse, "unidadTematica" | "tema">

const ordenados = (valores: string[]): string[] => [...new Set(valores)].sort()

/** Unidades temáticas distintas de las preguntas, ordenadas. */
export function unidadesDe(preguntas: ConUnidadYTema[]): string[] {
  return ordenados(preguntas.map((p) => p.unidadTematica))
}

/** Temas distintos de las preguntas de `unidad`; con la unidad vacía ("Todas"), los de todo el banco. */
export function temasDeUnidad(preguntas: ConUnidadYTema[], unidad: string): string[] {
  const delaUnidad = unidad ? preguntas.filter((p) => p.unidadTematica === unidad) : preguntas
  return ordenados(delaUnidad.map((p) => p.tema))
}

/** El tema a conservar al cambiar la unidad: el actual si la nueva unidad lo ofrece, si no "Todos" (vacío). */
export function temaTrasCambiarUnidad(
  preguntas: ConUnidadYTema[],
  unidad: string,
  temaActual: string,
): string {
  return temasDeUnidad(preguntas, unidad).includes(temaActual) ? temaActual : ""
}

/**
 * Sugerencias de Tema para un formulario donde la unidad se escribe o se elige (cargar y editar pregunta):
 * solo los temas de esa unidad. Con la unidad en blanco o una unidad nueva no hay sugerencias.
 */
export function sugerenciasDeTema(preguntas: ConUnidadYTema[], unidad: string): string[] {
  const escrita = unidad.trim()
  return escrita ? temasDeUnidad(preguntas, escrita) : []
}
