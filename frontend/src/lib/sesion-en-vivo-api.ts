import { apiFetch } from "@/lib/api-client"

export type EstadoSesionEnVivo = "en_espera" | "en_curso" | "finalizada"

export interface CrearSesionBody {
  comisionId: string
  cantidadPreguntas: number
  tiempoLimitePorPreguntaSegundos: number
  unidadTematica?: string | null
  tema?: string | null
}

export interface SesionEnVivoResponse {
  id: string
  comisionId: string
  materiaId: string
  unidadTematica: string | null
  tema: string | null
  cantidadPreguntas: number
  tiempoLimitePorPreguntaSegundos: number
  estado: EstadoSesionEnVivo
  preguntaActualIndice: number | null
}

export interface ParticipacionEnVivoResponse {
  sesionId: string
  estudianteId: string
  unidoEn: string
}

export interface RespuestaEnVivoResponse {
  esCorrecta: boolean
  puntaje: number
  puntajeAcumulado: number
}

export interface RespuestaCorrectaResponse {
  contenido: Record<string, unknown>
  texto: string
  opciones: string[] | null
}

export interface PreguntaActualResponse {
  preguntaId: string
  enunciado: string
  tipo: string
  opciones: string[] | null
  respuestaCorrecta: RespuestaCorrectaResponse | null
}

export interface OpcionDistribuidaResponse {
  opcion: string
  cantidad: number
}

export interface RankingItemResponse {
  posicion: number
  estudianteId: string
  puntajeAcumulado: number
  nombre: string
}

export interface ResultadoPreguntaResponse {
  distribucion: OpcionDistribuidaResponse[]
  ranking: RankingItemResponse[]
}

export interface EstadoSesionEnVivoResponse {
  estado: EstadoSesionEnVivo
  comisionId: string
  cantidadPreguntas: number
  tiempoLimitePorPreguntaSegundos: number
  preguntaActualIndice: number | null
  opcionesMostradas: boolean
  opcionesMostradasEn: string | null
  preguntaActualCerrada: boolean
  preguntaActual: PreguntaActualResponse | null
  yaRespondio: boolean | null
  puntajeAcumulado: number | null
  totalParticipantes: number
  cantidadRespuestas: number
  resultadoPregunta: ResultadoPreguntaResponse | null
}

export interface ParticipanteResponse {
  estudianteId: string
  unidoEn: string
  nombre: string
}

export interface SesionEnVivoResumenResponse {
  id: string
  comisionId: string
  materiaId: string
  materiaNombre: string
  cantidadPreguntas: number
  tiempoLimitePorPreguntaSegundos: number
  estado: EstadoSesionEnVivo
  unidadTematica: string | null
  tema: string | null
  creadaEn: string
}

interface SesionEnVivoApiResponse {
  id: string
  comision_id: string
  materia_id: string
  unidad_tematica: string | null
  tema: string | null
  cantidad_preguntas: number
  tiempo_limite_por_pregunta_segundos: number
  estado: EstadoSesionEnVivo
  pregunta_actual_indice: number | null
}

interface ParticipacionEnVivoApiResponse {
  sesion_id: string
  estudiante_id: string
  unido_en: string
}

interface RespuestaEnVivoApiResponse {
  es_correcta: boolean
  puntaje: number
  puntaje_acumulado: number
}

interface RespuestaCorrectaApiResponse {
  contenido: Record<string, unknown>
  texto: string
  opciones: string[] | null
}

interface PreguntaActualApiResponse {
  pregunta_id: string
  enunciado: string
  tipo: string
  opciones: string[] | null
  respuesta_correcta: RespuestaCorrectaApiResponse | null
}

interface OpcionDistribuidaApiResponse {
  opcion: string
  cantidad: number
}

interface RankingItemApiResponse {
  posicion: number
  estudiante_id: string
  puntaje_acumulado: number
  nombre: string
}

interface ResultadoPreguntaApiResponse {
  distribucion: OpcionDistribuidaApiResponse[]
  ranking: RankingItemApiResponse[]
}

interface EstadoSesionEnVivoApiResponse {
  estado: EstadoSesionEnVivo
  comision_id: string
  cantidad_preguntas: number
  tiempo_limite_por_pregunta_segundos: number
  pregunta_actual_indice: number | null
  opciones_mostradas: boolean
  opciones_mostradas_en: string | null
  pregunta_actual_cerrada: boolean
  pregunta_actual: PreguntaActualApiResponse | null
  ya_respondio: boolean | null
  puntaje_acumulado: number | null
  total_participantes: number
  cantidad_respuestas: number
  resultado_pregunta: ResultadoPreguntaApiResponse | null
}

interface ParticipanteApiResponse {
  estudiante_id: string
  unido_en: string
  nombre: string
}

interface SesionEnVivoResumenApiResponse {
  id: string
  comision_id: string
  materia_id: string
  materia_nombre: string
  cantidad_preguntas: number
  tiempo_limite_por_pregunta_segundos: number
  estado: EstadoSesionEnVivo
  unidad_tematica: string | null
  tema: string | null
  creada_en: string
}

function mapearSesion(sesion: SesionEnVivoApiResponse): SesionEnVivoResponse {
  return {
    id: sesion.id,
    comisionId: sesion.comision_id,
    materiaId: sesion.materia_id,
    unidadTematica: sesion.unidad_tematica,
    tema: sesion.tema,
    cantidadPreguntas: sesion.cantidad_preguntas,
    tiempoLimitePorPreguntaSegundos: sesion.tiempo_limite_por_pregunta_segundos,
    estado: sesion.estado,
    preguntaActualIndice: sesion.pregunta_actual_indice,
  }
}

function mapearParticipacion(
  participacion: ParticipacionEnVivoApiResponse,
): ParticipacionEnVivoResponse {
  return {
    sesionId: participacion.sesion_id,
    estudianteId: participacion.estudiante_id,
    unidoEn: participacion.unido_en,
  }
}

function mapearRespuesta(respuesta: RespuestaEnVivoApiResponse): RespuestaEnVivoResponse {
  return {
    esCorrecta: respuesta.es_correcta,
    puntaje: respuesta.puntaje,
    puntajeAcumulado: respuesta.puntaje_acumulado,
  }
}

function mapearRespuestaCorrecta(
  respuestaCorrecta: RespuestaCorrectaApiResponse,
): RespuestaCorrectaResponse {
  return {
    contenido: respuestaCorrecta.contenido,
    texto: respuestaCorrecta.texto,
    opciones: respuestaCorrecta.opciones,
  }
}

function mapearPreguntaActual(pregunta: PreguntaActualApiResponse): PreguntaActualResponse {
  return {
    preguntaId: pregunta.pregunta_id,
    enunciado: pregunta.enunciado,
    tipo: pregunta.tipo,
    opciones: pregunta.opciones,
    respuestaCorrecta: pregunta.respuesta_correcta
      ? mapearRespuestaCorrecta(pregunta.respuesta_correcta)
      : null,
  }
}

function mapearRankingItem(item: RankingItemApiResponse): RankingItemResponse {
  return {
    posicion: item.posicion,
    estudianteId: item.estudiante_id,
    puntajeAcumulado: item.puntaje_acumulado,
    nombre: item.nombre,
  }
}

function mapearResultadoPregunta(
  resultado: ResultadoPreguntaApiResponse,
): ResultadoPreguntaResponse {
  return {
    distribucion: resultado.distribucion.map((fila) => ({
      opcion: fila.opcion,
      cantidad: fila.cantidad,
    })),
    ranking: resultado.ranking.map(mapearRankingItem),
  }
}

function mapearEstadoSesion(estado: EstadoSesionEnVivoApiResponse): EstadoSesionEnVivoResponse {
  return {
    estado: estado.estado,
    comisionId: estado.comision_id,
    cantidadPreguntas: estado.cantidad_preguntas,
    tiempoLimitePorPreguntaSegundos: estado.tiempo_limite_por_pregunta_segundos,
    preguntaActualIndice: estado.pregunta_actual_indice,
    opcionesMostradas: estado.opciones_mostradas,
    opcionesMostradasEn: estado.opciones_mostradas_en,
    preguntaActualCerrada: estado.pregunta_actual_cerrada,
    preguntaActual: estado.pregunta_actual ? mapearPreguntaActual(estado.pregunta_actual) : null,
    yaRespondio: estado.ya_respondio,
    puntajeAcumulado: estado.puntaje_acumulado,
    totalParticipantes: estado.total_participantes,
    cantidadRespuestas: estado.cantidad_respuestas,
    resultadoPregunta: estado.resultado_pregunta
      ? mapearResultadoPregunta(estado.resultado_pregunta)
      : null,
  }
}

function mapearParticipante(participante: ParticipanteApiResponse): ParticipanteResponse {
  return {
    estudianteId: participante.estudiante_id,
    unidoEn: participante.unido_en,
    nombre: participante.nombre,
  }
}

function mapearSesionResumen(
  resumen: SesionEnVivoResumenApiResponse,
): SesionEnVivoResumenResponse {
  return {
    id: resumen.id,
    comisionId: resumen.comision_id,
    materiaId: resumen.materia_id,
    materiaNombre: resumen.materia_nombre,
    cantidadPreguntas: resumen.cantidad_preguntas,
    tiempoLimitePorPreguntaSegundos: resumen.tiempo_limite_por_pregunta_segundos,
    estado: resumen.estado,
    unidadTematica: resumen.unidad_tematica,
    tema: resumen.tema,
    creadaEn: resumen.creada_en,
  }
}

/** Cliente API del modo en vivo — reutiliza `apiFetch` (JWT/401/403 de `US-1.1.6`). */

export async function crearSesion(
  body: CrearSesionBody,
  signal?: AbortSignal,
): Promise<SesionEnVivoResponse> {
  const response = await apiFetch<SesionEnVivoApiResponse>("/sesiones-en-vivo", {
    method: "POST",
    body: {
      comision_id: body.comisionId,
      cantidad_preguntas: body.cantidadPreguntas,
      tiempo_limite_por_pregunta_segundos: body.tiempoLimitePorPreguntaSegundos,
      unidad_tematica: body.unidadTematica ?? null,
      tema: body.tema ?? null,
    },
    signal,
  })
  return mapearSesion(response)
}

export async function iniciarSesion(
  sesionId: string,
  signal?: AbortSignal,
): Promise<SesionEnVivoResponse> {
  const response = await apiFetch<SesionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/iniciar`,
    { method: "POST", signal },
  )
  return mapearSesion(response)
}

export async function mostrarOpciones(
  sesionId: string,
  signal?: AbortSignal,
): Promise<SesionEnVivoResponse> {
  const response = await apiFetch<SesionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/mostrar-opciones`,
    { method: "POST", signal },
  )
  return mapearSesion(response)
}

export async function cerrarPregunta(
  sesionId: string,
  signal?: AbortSignal,
): Promise<SesionEnVivoResponse> {
  const response = await apiFetch<SesionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/cerrar-pregunta`,
    { method: "POST", signal },
  )
  return mapearSesion(response)
}

export async function avanzarPregunta(
  sesionId: string,
  signal?: AbortSignal,
): Promise<SesionEnVivoResponse> {
  const response = await apiFetch<SesionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/avanzar`,
    { method: "POST", signal },
  )
  return mapearSesion(response)
}

export async function finalizarSesion(
  sesionId: string,
  signal?: AbortSignal,
): Promise<SesionEnVivoResponse> {
  const response = await apiFetch<SesionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/finalizar`,
    { method: "POST", signal },
  )
  return mapearSesion(response)
}

export async function unirseASesion(
  sesionId: string,
  signal?: AbortSignal,
): Promise<ParticipacionEnVivoResponse> {
  const response = await apiFetch<ParticipacionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/unirse`,
    { method: "POST", signal },
  )
  return mapearParticipacion(response)
}

export async function responderPregunta(
  sesionId: string,
  preguntaId: string,
  contenido: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<RespuestaEnVivoResponse> {
  const response = await apiFetch<RespuestaEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}/responder`,
    { method: "POST", body: { pregunta_id: preguntaId, contenido }, signal },
  )
  return mapearRespuesta(response)
}

export async function obtenerEstadoSesion(
  sesionId: string,
  signal?: AbortSignal,
): Promise<EstadoSesionEnVivoResponse> {
  const response = await apiFetch<EstadoSesionEnVivoApiResponse>(
    `/sesiones-en-vivo/${sesionId}`,
    { signal },
  )
  return mapearEstadoSesion(response)
}

export async function listarParticipantes(
  sesionId: string,
  signal?: AbortSignal,
): Promise<ParticipanteResponse[]> {
  const response = await apiFetch<ParticipanteApiResponse[]>(
    `/sesiones-en-vivo/${sesionId}/participantes`,
    { signal },
  )
  return response.map(mapearParticipante)
}

export async function obtenerRankingSesion(
  sesionId: string,
  signal?: AbortSignal,
): Promise<RankingItemResponse[]> {
  const response = await apiFetch<RankingItemApiResponse[]>(
    `/sesiones-en-vivo/${sesionId}/ranking`,
    { signal },
  )
  return response.map(mapearRankingItem)
}

export async function listarSesionesEnVivo(
  comisionId: string,
  signal?: AbortSignal,
): Promise<SesionEnVivoResumenResponse[]> {
  const params = new URLSearchParams({ comision_id: comisionId })
  const response = await apiFetch<SesionEnVivoResumenApiResponse[]>(
    `/sesiones-en-vivo?${params}`,
    { signal },
  )
  return response.map(mapearSesionResumen)
}
