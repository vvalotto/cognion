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
