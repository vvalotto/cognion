import { apiFetch } from "@/lib/api-client"

export interface EvaluacionDesempenoResponse {
  evaluacionId: string
  actividadId: string
  finalizadaEn: string
  cantidadCorrectas: number
  cantidadIncorrectas: number
}

export interface ResumenDesempenoResponse {
  totalCorrectas: number
  totalIncorrectas: number
  porcentajeAcierto: number
  cantidadEvaluaciones: number
}

export interface DesempenoEstudianteResponse {
  evaluaciones: EvaluacionDesempenoResponse[]
  resumen: ResumenDesempenoResponse
}

export interface TasaErrorTemaResponse {
  unidadTematica: string
  tema: string
  cantidadRespuestas: number
  cantidadIncorrectas: number
  tasaError: number
}

export interface DesempenoComisionFilaResponse {
  estudianteId: string
  nombre: string
  porcentajeAciertosAcumulado: number | null
  actividadesPendientes: number
}

export interface EvolucionTemporalPuntoResponse {
  actividadId: string
  tituloActividad: string
  finalizadaEn: string
  porcentajeAcierto: number
}

export interface EvolucionTemporalComisionPuntoResponse {
  actividadId: string
  tituloActividad: string
  porcentajeAciertosPromedio: number
}

export interface RankingPreguntaFalladaResponse {
  preguntaId: string
  enunciado: string
  unidadTematica: string
  tema: string
  cantidadPresentaciones: number
  cantidadFallos: number
  tasaError: number
}

export interface CompletitudFilaResponse {
  estudianteId: string
  nombre: string
  estado: string
}

export interface CompletitudResumenResponse {
  finalizadas: number
  enCurso: number
  suspendidas: number
  sinIniciar: number
}

export interface CompletitudPorActividadResponse {
  detalle: CompletitudFilaResponse[]
  resumen: CompletitudResumenResponse
}

interface EvaluacionDesempenoApiResponse {
  evaluacion_id: string
  actividad_id: string
  finalizada_en: string
  cantidad_correctas: number
  cantidad_incorrectas: number
}

interface ResumenDesempenoApiResponse {
  total_correctas: number
  total_incorrectas: number
  porcentaje_acierto: number
  cantidad_evaluaciones: number
}

interface DesempenoEstudianteApiResponse {
  evaluaciones: EvaluacionDesempenoApiResponse[]
  resumen: ResumenDesempenoApiResponse
}

interface TasaErrorTemaApiResponse {
  unidad_tematica: string
  tema: string
  cantidad_respuestas: number
  cantidad_incorrectas: number
  tasa_error: number
}

interface DesempenoComisionFilaApiResponse {
  estudiante_id: string
  nombre: string
  porcentaje_aciertos_acumulado: number | null
  actividades_pendientes: number
}

interface EvolucionTemporalPuntoApiResponse {
  actividad_id: string
  titulo_actividad: string
  finalizada_en: string
  porcentaje_acierto: number
}

interface EvolucionTemporalComisionPuntoApiResponse {
  actividad_id: string
  titulo_actividad: string
  porcentaje_aciertos_promedio: number
}

interface CompletitudFilaApiResponse {
  estudiante_id: string
  nombre: string
  estado: string
}

interface CompletitudResumenApiResponse {
  finalizadas: number
  en_curso: number
  suspendidas: number
  sin_iniciar: number
}

interface CompletitudPorActividadApiResponse {
  detalle: CompletitudFilaApiResponse[]
  resumen: CompletitudResumenApiResponse
}

interface RankingPreguntaFalladaApiResponse {
  pregunta_id: string
  enunciado: string
  unidad_tematica: string
  tema: string
  cantidad_presentaciones: number
  cantidad_fallos: number
  tasa_error: number
}

function mapearDesempenoEstudiante(
  response: DesempenoEstudianteApiResponse,
): DesempenoEstudianteResponse {
  return {
    evaluaciones: response.evaluaciones.map((e) => ({
      evaluacionId: e.evaluacion_id,
      actividadId: e.actividad_id,
      finalizadaEn: e.finalizada_en,
      cantidadCorrectas: e.cantidad_correctas,
      cantidadIncorrectas: e.cantidad_incorrectas,
    })),
    resumen: {
      totalCorrectas: response.resumen.total_correctas,
      totalIncorrectas: response.resumen.total_incorrectas,
      porcentajeAcierto: response.resumen.porcentaje_acierto,
      cantidadEvaluaciones: response.resumen.cantidad_evaluaciones,
    },
  }
}

/** Cliente API de consulta de desempeño del Estudiante en BC Analytics (`US-4.1.2`). */
export async function obtenerMiDesempeno(
  materiaId: string,
  signal?: AbortSignal,
): Promise<DesempenoEstudianteResponse> {
  const response = await apiFetch<DesempenoEstudianteApiResponse>(
    `/analytics/materias/${materiaId}/mi-desempeno`,
    { signal },
  )
  return mapearDesempenoEstudiante(response)
}

/** Cliente API de consulta del Docente al desempeño de un Estudiante elegido (`US-4.2.1`, RF-16). */
export async function obtenerDesempenoDeEstudiante(
  materiaId: string,
  estudianteId: string,
  signal?: AbortSignal,
): Promise<DesempenoEstudianteResponse> {
  const response = await apiFetch<DesempenoEstudianteApiResponse>(
    `/analytics/materias/${materiaId}/estudiantes/${estudianteId}/desempeno`,
    { signal },
  )
  return mapearDesempenoEstudiante(response)
}

function mapearTasaErrorTema(response: TasaErrorTemaApiResponse): TasaErrorTemaResponse {
  return {
    unidadTematica: response.unidad_tematica,
    tema: response.tema,
    cantidadRespuestas: response.cantidad_respuestas,
    cantidadIncorrectas: response.cantidad_incorrectas,
    tasaError: response.tasa_error,
  }
}

/** Cliente API de tasa de error por unidad/tema de una materia, agregada o por comisión (`US-4.2.4`, RF-17). */
export async function obtenerTasaErrorPorTema(
  materiaId: string,
  comisionId?: string,
  signal?: AbortSignal,
): Promise<TasaErrorTemaResponse[]> {
  const query = comisionId ? `?comision_id=${comisionId}` : ""
  const response = await apiFetch<TasaErrorTemaApiResponse[]>(
    `/analytics/materias/${materiaId}/tasa-error-por-tema${query}`,
    { signal },
  )
  return response.map(mapearTasaErrorTema)
}

function mapearDesempenoComisionFila(
  response: DesempenoComisionFilaApiResponse,
): DesempenoComisionFilaResponse {
  return {
    estudianteId: response.estudiante_id,
    nombre: response.nombre,
    porcentajeAciertosAcumulado: response.porcentaje_aciertos_acumulado,
    actividadesPendientes: response.actividades_pendientes,
  }
}

/** Cliente API de desempeño de todos los estudiantes de una comisión (`US-ADJ-44`, RF-20). */
export async function obtenerDesempenoPorComision(
  materiaId: string,
  comisionId: string,
  signal?: AbortSignal,
): Promise<DesempenoComisionFilaResponse[]> {
  const response = await apiFetch<DesempenoComisionFilaApiResponse[]>(
    `/analytics/materias/${materiaId}/comisiones/${comisionId}/desempeno`,
    { signal },
  )
  return response.map(mapearDesempenoComisionFila)
}

function mapearEvolucionTemporalPunto(
  response: EvolucionTemporalPuntoApiResponse,
): EvolucionTemporalPuntoResponse {
  return {
    actividadId: response.actividad_id,
    tituloActividad: response.titulo_actividad,
    finalizadaEn: response.finalizada_en,
    porcentajeAcierto: response.porcentaje_acierto,
  }
}

/** Cliente API de evolución temporal individual de un estudiante (`US-ADJ-45`, RF-21). */
export async function obtenerEvolucionTemporalEstudiante(
  materiaId: string,
  estudianteId: string,
  signal?: AbortSignal,
): Promise<EvolucionTemporalPuntoResponse[]> {
  const response = await apiFetch<EvolucionTemporalPuntoApiResponse[]>(
    `/analytics/materias/${materiaId}/estudiantes/${estudianteId}/evolucion-temporal`,
    { signal },
  )
  return response.map(mapearEvolucionTemporalPunto)
}

function mapearEvolucionTemporalComisionPunto(
  response: EvolucionTemporalComisionPuntoApiResponse,
): EvolucionTemporalComisionPuntoResponse {
  return {
    actividadId: response.actividad_id,
    tituloActividad: response.titulo_actividad,
    porcentajeAciertosPromedio: response.porcentaje_aciertos_promedio,
  }
}

/** Cliente API de evolución temporal promedio de una comisión (`US-ADJ-45`, RF-21). */
export async function obtenerEvolucionTemporalComision(
  materiaId: string,
  comisionId: string,
  signal?: AbortSignal,
): Promise<EvolucionTemporalComisionPuntoResponse[]> {
  const response = await apiFetch<EvolucionTemporalComisionPuntoApiResponse[]>(
    `/analytics/materias/${materiaId}/comisiones/${comisionId}/evolucion-temporal`,
    { signal },
  )
  return response.map(mapearEvolucionTemporalComisionPunto)
}

function mapearRankingPreguntaFallada(
  response: RankingPreguntaFalladaApiResponse,
): RankingPreguntaFalladaResponse {
  return {
    preguntaId: response.pregunta_id,
    enunciado: response.enunciado,
    unidadTematica: response.unidad_tematica,
    tema: response.tema,
    cantidadPresentaciones: response.cantidad_presentaciones,
    cantidadFallos: response.cantidad_fallos,
    tasaError: response.tasa_error,
  }
}

/** Cliente API de ranking de preguntas más falladas de una materia, agregado o por comisión (`US-ADJ-46`, RF-22). */
export async function obtenerRankingPreguntasFalladas(
  materiaId: string,
  comisionId?: string,
  signal?: AbortSignal,
): Promise<RankingPreguntaFalladaResponse[]> {
  const query = comisionId ? `?comision_id=${comisionId}` : ""
  const response = await apiFetch<RankingPreguntaFalladaApiResponse[]>(
    `/analytics/materias/${materiaId}/ranking-preguntas-falladas${query}`,
    { signal },
  )
  return response.map(mapearRankingPreguntaFallada)
}

function mapearCompletitudPorActividad(
  response: CompletitudPorActividadApiResponse,
): CompletitudPorActividadResponse {
  return {
    detalle: response.detalle.map((fila) => ({
      estudianteId: fila.estudiante_id,
      nombre: fila.nombre,
      estado: fila.estado,
    })),
    resumen: {
      finalizadas: response.resumen.finalizadas,
      enCurso: response.resumen.en_curso,
      suspendidas: response.resumen.suspendidas,
      sinIniciar: response.resumen.sin_iniciar,
    },
  }
}

/** Cliente API de completitud de una actividad puntual (`US-ADJ-51`, RF-23). */
export async function obtenerCompletitudPorActividad(
  actividadId: string,
  signal?: AbortSignal,
): Promise<CompletitudPorActividadResponse> {
  const response = await apiFetch<CompletitudPorActividadApiResponse>(
    `/analytics/actividades/${actividadId}/completitud`,
    { signal },
  )
  return mapearCompletitudPorActividad(response)
}
