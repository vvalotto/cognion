import { apiFetch } from "@/lib/api-client"

export interface CrearActividadBody {
  materiaId: string
  fechaApertura: string
  fechaCierre: string
  cantidadPreguntas: number
  cantidadIntentosPermitidos: number
}

export interface ActividadResponse {
  id: string
  materiaId: string
  fechaApertura: string
  fechaCierre: string
  cantidadPreguntas: number
  cantidadIntentosPermitidos: number
  cerradaManualmente: boolean
}

export interface PreguntaAsignadaResponse {
  preguntaId: string
  orden: number
}

export interface EvaluacionResponse {
  id: string
  actividadId: string
  estudianteId: string
  preguntasAsignadas: PreguntaAsignadaResponse[]
  estado: string
  iniciadaEn: string
}

export interface RespuestaResponse {
  id: string
  preguntaId: string
  numeroIntento: number
  confirmadaEn: string
}

export interface DetallePreguntaRevisionResponse {
  preguntaId: string
  orden: number
  texto: string
  respondida: boolean
  contenidoPropio: Record<string, unknown> | null
  esCorrecta: boolean
  contenidoCorrecto: Record<string, unknown> | null
}

export interface RevisionEvaluacionResponse {
  evaluacionId: string
  cantidadPreguntas: number
  cantidadCorrectas: number
  cantidadIncorrectas: number
  detalle: DetallePreguntaRevisionResponse[]
}

interface ActividadApiResponse {
  id: string
  materia_id: string
  fecha_apertura: string
  fecha_cierre: string
  cantidad_preguntas: number
  cantidad_intentos_permitidos: number
  cerrada_manualmente: boolean
}

interface PreguntaAsignadaApiResponse {
  pregunta_id: string
  orden: number
}

interface EvaluacionApiResponse {
  id: string
  actividad_id: string
  estudiante_id: string
  preguntas_asignadas: PreguntaAsignadaApiResponse[]
  estado: string
  iniciada_en: string
}

interface RespuestaApiResponse {
  id: string
  pregunta_id: string
  numero_intento: number
  confirmada_en: string
}

interface DetallePreguntaRevisionApiResponse {
  pregunta_id: string
  orden: number
  texto: string
  respondida: boolean
  contenido_propio: Record<string, unknown> | null
  es_correcta: boolean
  contenido_correcto: Record<string, unknown> | null
}

interface RevisionEvaluacionApiResponse {
  evaluacion_id: string
  cantidad_preguntas: number
  cantidad_correctas: number
  cantidad_incorrectas: number
  detalle: DetallePreguntaRevisionApiResponse[]
}

function mapearActividad(actividad: ActividadApiResponse): ActividadResponse {
  return {
    id: actividad.id,
    materiaId: actividad.materia_id,
    fechaApertura: actividad.fecha_apertura,
    fechaCierre: actividad.fecha_cierre,
    cantidadPreguntas: actividad.cantidad_preguntas,
    cantidadIntentosPermitidos: actividad.cantidad_intentos_permitidos,
    cerradaManualmente: actividad.cerrada_manualmente,
  }
}

function mapearEvaluacion(evaluacion: EvaluacionApiResponse): EvaluacionResponse {
  return {
    id: evaluacion.id,
    actividadId: evaluacion.actividad_id,
    estudianteId: evaluacion.estudiante_id,
    preguntasAsignadas: evaluacion.preguntas_asignadas.map((p) => ({
      preguntaId: p.pregunta_id,
      orden: p.orden,
    })),
    estado: evaluacion.estado,
    iniciadaEn: evaluacion.iniciada_en,
  }
}

function mapearRevision(revision: RevisionEvaluacionApiResponse): RevisionEvaluacionResponse {
  return {
    evaluacionId: revision.evaluacion_id,
    cantidadPreguntas: revision.cantidad_preguntas,
    cantidadCorrectas: revision.cantidad_correctas,
    cantidadIncorrectas: revision.cantidad_incorrectas,
    detalle: revision.detalle.map((fila) => ({
      preguntaId: fila.pregunta_id,
      orden: fila.orden,
      texto: fila.texto,
      respondida: fila.respondida,
      contenidoPropio: fila.contenido_propio,
      esCorrecta: fila.es_correcta,
      contenidoCorrecto: fila.contenido_correcto,
    })),
  }
}

/** Cliente API del BC Actividad Evaluativa — reutiliza `apiFetch` (JWT/401/403 de `US-1.1.6`). */

export async function crearActividad(body: CrearActividadBody): Promise<ActividadResponse> {
  const response = await apiFetch<ActividadApiResponse>("/actividades", {
    method: "POST",
    body: {
      materia_id: body.materiaId,
      fecha_apertura: body.fechaApertura,
      fecha_cierre: body.fechaCierre,
      cantidad_preguntas: body.cantidadPreguntas,
      cantidad_intentos_permitidos: body.cantidadIntentosPermitidos,
    },
  })
  return mapearActividad(response)
}

export async function modificarPeriodoDisponibilidad(
  actividadId: string,
  nuevaFechaCierre: string,
): Promise<ActividadResponse> {
  const response = await apiFetch<ActividadApiResponse>(`/actividades/${actividadId}/periodo`, {
    method: "PATCH",
    body: { nueva_fecha_cierre: nuevaFechaCierre },
  })
  return mapearActividad(response)
}

export async function cerrarActividad(actividadId: string): Promise<ActividadResponse> {
  const response = await apiFetch<ActividadApiResponse>(`/actividades/${actividadId}/cerrar`, {
    method: "POST",
  })
  return mapearActividad(response)
}

export async function iniciarEvaluacion(actividadId: string): Promise<EvaluacionResponse> {
  const response = await apiFetch<EvaluacionApiResponse>("/evaluaciones", {
    method: "POST",
    body: { actividad_id: actividadId },
  })
  return mapearEvaluacion(response)
}

export async function registrarRespuesta(
  evaluacionId: string,
  preguntaId: string,
  contenido: Record<string, unknown>,
): Promise<RespuestaResponse> {
  const response = await apiFetch<RespuestaApiResponse>(
    `/evaluaciones/${evaluacionId}/respuestas`,
    { method: "POST", body: { pregunta_id: preguntaId, contenido } },
  )
  return {
    id: response.id,
    preguntaId: response.pregunta_id,
    numeroIntento: response.numero_intento,
    confirmadaEn: response.confirmada_en,
  }
}

export async function suspenderEvaluacion(evaluacionId: string): Promise<EvaluacionResponse> {
  const response = await apiFetch<EvaluacionApiResponse>(
    `/evaluaciones/${evaluacionId}/suspender`,
    { method: "POST" },
  )
  return mapearEvaluacion(response)
}

export async function reanudarEvaluacion(evaluacionId: string): Promise<EvaluacionResponse> {
  const response = await apiFetch<EvaluacionApiResponse>(
    `/evaluaciones/${evaluacionId}/reanudar`,
    { method: "POST" },
  )
  return mapearEvaluacion(response)
}

export async function finalizarEvaluacion(evaluacionId: string): Promise<EvaluacionResponse> {
  const response = await apiFetch<EvaluacionApiResponse>(
    `/evaluaciones/${evaluacionId}/finalizar`,
    { method: "POST" },
  )
  return mapearEvaluacion(response)
}

export async function obtenerRevision(evaluacionId: string): Promise<RevisionEvaluacionResponse> {
  const response = await apiFetch<RevisionEvaluacionApiResponse>(
    `/evaluaciones/${evaluacionId}/revision`,
  )
  return mapearRevision(response)
}
