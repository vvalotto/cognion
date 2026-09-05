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

/** Cliente API de consulta de desempeño del Estudiante en BC Analytics (`US-4.1.2`). */
export async function obtenerMiDesempeno(
  materiaId: string,
  signal?: AbortSignal,
): Promise<DesempenoEstudianteResponse> {
  const response = await apiFetch<DesempenoEstudianteApiResponse>(
    `/analytics/materias/${materiaId}/mi-desempeno`,
    { signal },
  )
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
