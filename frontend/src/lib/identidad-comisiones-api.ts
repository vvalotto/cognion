import { apiFetch } from "@/lib/api-client"

export interface ComisionResumenResponse {
  id: string
  horario: string
}

export interface EstudianteResumenResponse {
  id: string
  nombre: string
}

/** Cliente API de consulta de comisiones/estudiantes por el Docente en BC Identidad (`US-4.2.2`). */
export async function listarComisionesPorMateria(
  materiaId: string,
  signal?: AbortSignal,
): Promise<ComisionResumenResponse[]> {
  return apiFetch<ComisionResumenResponse[]>(`/materias/${materiaId}/comisiones`, { signal })
}

export async function listarEstudiantesDeComision(
  comisionId: string,
  signal?: AbortSignal,
): Promise<EstudianteResumenResponse[]> {
  return apiFetch<EstudianteResumenResponse[]>(`/comisiones/${comisionId}/estudiantes`, {
    signal,
  })
}
