import { apiFetch } from "@/lib/api-client"
import { obtenerUsuarioId } from "@/lib/session"

export interface ComisionResumenResponse {
  id: string
  horario: string
  docentesAsignados: string[]
}

interface ComisionResumenApiResponse {
  id: string
  horario: string
  docentes_asignados: string[]
}

export interface EstudianteResumenResponse {
  id: string
  nombre: string
}

/**
 * Cliente API de consulta de comisiones/estudiantes (`US-4.2.2`, consumido por
 * Docente/Analytics) — `docentesAsignados` agregado en `US-ADJ-23` para la pantalla de
 * Comisiones del Administrador.
 */
export async function listarComisionesPorMateria(
  materiaId: string,
  signal?: AbortSignal,
): Promise<ComisionResumenResponse[]> {
  const response = await apiFetch<ComisionResumenApiResponse[]>(
    `/materias/${materiaId}/comisiones`,
    { signal },
  )
  return response.map((comision) => ({
    id: comision.id,
    horario: comision.horario,
    docentesAsignados: comision.docentes_asignados,
  }))
}

export async function listarEstudiantesDeComision(
  comisionId: string,
  signal?: AbortSignal,
): Promise<EstudianteResumenResponse[]> {
  return apiFetch<EstudianteResumenResponse[]>(`/comisiones/${comisionId}/estudiantes`, {
    signal,
  })
}

interface ComisionResponse {
  id: string
}

/**
 * Crea una comisión (`US-ADJ-24`) — `administrador_id` se resuelve del JWT de la sesión
 * actual, sin pedírselo al usuario en el formulario.
 */
export async function crearComision(
  materiaId: string,
  horario: string,
  signal?: AbortSignal,
): Promise<ComisionResponse> {
  return apiFetch<ComisionResponse>("/comisiones", {
    method: "POST",
    body: {
      materia_id: materiaId,
      horario,
      administrador_id: obtenerUsuarioId(),
    },
    signal,
  })
}
