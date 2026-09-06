import { apiFetch } from "@/lib/api-client"

export type Dificultad = "alto" | "medio" | "bajo"
export type Importancia = "alto" | "medio" | "bajo"

export interface MateriaResponse {
  id: string
  nombre: string
  bancoId: string
}

export interface MateriaListItemResponse {
  id: string
  nombre: string
  bancoId: string
  cantidadPreguntasActivas: number
}

export interface Opcion {
  texto: string
  esCorrecta: boolean
}

export interface PreguntaOpcionMultipleResponse {
  id: string
  bancoId: string
  texto: string
  opciones: Opcion[]
  unidadTematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
  activa: boolean
}

export interface PreguntaVerdaderoFalsoResponse {
  id: string
  bancoId: string
  texto: string
  respuestaCorrecta: boolean
  unidadTematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
  activa: boolean
}

export type PreguntaResponse = PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse

export interface FiltrosBanco {
  unidad?: string
  tema?: string
  dificultad?: Dificultad
  importancia?: Importancia
}

/** Opt-in (US-ADJ-03): si se omiten, `filtrarBanco` devuelve el banco completo sin paginar. */
export interface PaginacionBanco {
  pagina: number
  tamanioPagina: number
}

export interface PreguntasPaginadas {
  preguntas: PreguntaResponse[]
  total: number
}

export interface CargarPreguntaOpcionMultipleBody {
  bancoId: string
  texto: string
  opciones: Opcion[]
  unidadTematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
}

export interface CargarPreguntaVerdaderoFalsoBody {
  bancoId: string
  texto: string
  respuestaCorrecta: boolean
  unidadTematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
}

export interface EditarPreguntaBody {
  texto: string
  unidadTematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
  opciones?: Opcion[]
  respuestaCorrecta?: boolean
}

interface MateriaApiResponse {
  id: string
  nombre: string
  banco_id: string
}

interface MateriaListItemApiResponse {
  id: string
  nombre: string
  banco_id: string
  cantidad_preguntas_activas: number
}

interface OpcionApiSchema {
  texto: string
  es_correcta: boolean
}

interface PreguntaOpcionMultipleApiResponse {
  id: string
  banco_id: string
  texto: string
  opciones: OpcionApiSchema[]
  unidad_tematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
  activa: boolean
}

interface PreguntaVerdaderoFalsoApiResponse {
  id: string
  banco_id: string
  texto: string
  respuesta_correcta: boolean
  unidad_tematica: string
  tema: string
  dificultad: Dificultad
  importancia: Importancia
  activa: boolean
}

type PreguntaApiResponse = PreguntaOpcionMultipleApiResponse | PreguntaVerdaderoFalsoApiResponse

interface PreguntasPaginadasApiResponse {
  preguntas: PreguntaApiResponse[]
  total: number
}

function esOpcionMultipleApi(
  pregunta: PreguntaApiResponse,
): pregunta is PreguntaOpcionMultipleApiResponse {
  return "opciones" in pregunta
}

function mapearPregunta(pregunta: PreguntaApiResponse): PreguntaResponse {
  if (esOpcionMultipleApi(pregunta)) {
    return {
      id: pregunta.id,
      bancoId: pregunta.banco_id,
      texto: pregunta.texto,
      opciones: pregunta.opciones.map((o) => ({ texto: o.texto, esCorrecta: o.es_correcta })),
      unidadTematica: pregunta.unidad_tematica,
      tema: pregunta.tema,
      dificultad: pregunta.dificultad,
      importancia: pregunta.importancia,
      activa: pregunta.activa,
    }
  }
  return {
    id: pregunta.id,
    bancoId: pregunta.banco_id,
    texto: pregunta.texto,
    respuestaCorrecta: pregunta.respuesta_correcta,
    unidadTematica: pregunta.unidad_tematica,
    tema: pregunta.tema,
    dificultad: pregunta.dificultad,
    importancia: pregunta.importancia,
    activa: pregunta.activa,
  }
}

/** Cliente API del BC Banco de Preguntas — reutiliza `apiFetch` (JWT/401/403 de `US-1.1.6`). */

export async function crearMateria(
  nombre: string,
  signal?: AbortSignal,
): Promise<MateriaResponse> {
  const response = await apiFetch<MateriaApiResponse>("/materias", {
    method: "POST",
    body: { nombre },
    signal,
  })
  return { id: response.id, nombre: response.nombre, bancoId: response.banco_id }
}

export async function listarMaterias(signal?: AbortSignal): Promise<MateriaListItemResponse[]> {
  const response = await apiFetch<MateriaListItemApiResponse[]>("/materias", { signal })
  return response.map((materia) => ({
    id: materia.id,
    nombre: materia.nombre,
    bancoId: materia.banco_id,
    cantidadPreguntasActivas: materia.cantidad_preguntas_activas,
  }))
}

export async function filtrarBanco(
  bancoId: string,
  filtros: FiltrosBanco = {},
  paginacion?: PaginacionBanco,
  signal?: AbortSignal,
): Promise<PreguntasPaginadas> {
  const params = new URLSearchParams()
  if (filtros.unidad) params.set("unidad", filtros.unidad)
  if (filtros.tema) params.set("tema", filtros.tema)
  if (filtros.dificultad) params.set("dificultad", filtros.dificultad)
  if (filtros.importancia) params.set("importancia", filtros.importancia)
  if (paginacion) {
    params.set("pagina", String(paginacion.pagina))
    params.set("tamanio_pagina", String(paginacion.tamanioPagina))
  }

  const query = params.toString()
  const response = await apiFetch<PreguntasPaginadasApiResponse>(
    `/bancos/${bancoId}/preguntas${query ? `?${query}` : ""}`,
    { signal },
  )
  return { preguntas: response.preguntas.map(mapearPregunta), total: response.total }
}

export async function cargarPreguntaOpcionMultiple(
  body: CargarPreguntaOpcionMultipleBody,
  signal?: AbortSignal,
): Promise<PreguntaOpcionMultipleResponse> {
  const response = await apiFetch<PreguntaOpcionMultipleApiResponse>("/preguntas/opcion-multiple", {
    method: "POST",
    body: {
      banco_id: body.bancoId,
      texto: body.texto,
      opciones: body.opciones.map((o) => ({ texto: o.texto, es_correcta: o.esCorrecta })),
      unidad_tematica: body.unidadTematica,
      tema: body.tema,
      dificultad: body.dificultad,
      importancia: body.importancia,
    },
    signal,
  })
  return mapearPregunta(response) as PreguntaOpcionMultipleResponse
}

export async function cargarPreguntaVerdaderoFalso(
  body: CargarPreguntaVerdaderoFalsoBody,
  signal?: AbortSignal,
): Promise<PreguntaVerdaderoFalsoResponse> {
  const response = await apiFetch<PreguntaVerdaderoFalsoApiResponse>("/preguntas/verdadero-falso", {
    method: "POST",
    body: {
      banco_id: body.bancoId,
      texto: body.texto,
      respuesta_correcta: body.respuestaCorrecta,
      unidad_tematica: body.unidadTematica,
      tema: body.tema,
      dificultad: body.dificultad,
      importancia: body.importancia,
    },
    signal,
  })
  return mapearPregunta(response) as PreguntaVerdaderoFalsoResponse
}

export async function editarPregunta(
  preguntaId: string,
  body: EditarPreguntaBody,
  signal?: AbortSignal,
): Promise<PreguntaResponse> {
  const response = await apiFetch<PreguntaApiResponse>(`/preguntas/${preguntaId}`, {
    method: "PUT",
    body: {
      texto: body.texto,
      unidad_tematica: body.unidadTematica,
      tema: body.tema,
      dificultad: body.dificultad,
      importancia: body.importancia,
      opciones: body.opciones?.map((o) => ({ texto: o.texto, es_correcta: o.esCorrecta })),
      respuesta_correcta: body.respuestaCorrecta,
    },
    signal,
  })
  return mapearPregunta(response)
}

export async function eliminarPregunta(preguntaId: string, signal?: AbortSignal): Promise<void> {
  await apiFetch<void>(`/preguntas/${preguntaId}`, { method: "DELETE", signal })
}

/** Valores únicos de unidad temática y tema ya usados en el banco — sugerencias de combobox (US-ADJ-02). */
export function derivarSugerencias(preguntas: PreguntaResponse[]): {
  unidades: string[]
  temas: string[]
} {
  return {
    unidades: [...new Set(preguntas.map((p) => p.unidadTematica))].sort(),
    temas: [...new Set(preguntas.map((p) => p.tema))].sort(),
  }
}
