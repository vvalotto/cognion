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

export interface ComisionDetalleResponse {
  id: string
  horario: string
  docentesAsignados: string[]
}

interface ComisionDetalleApiResponse {
  id: string
  materia_id: string
  horario: string
  administrador_id: string
  docentes_asignados: string[]
}

function mapearDetalle(response: ComisionDetalleApiResponse): ComisionDetalleResponse {
  return {
    id: response.id,
    horario: response.horario,
    docentesAsignados: response.docentes_asignados,
  }
}

/** Detalle de una comisión puntual (`US-ADJ-25`) — horario + docentes asignados. */
export async function obtenerComision(
  comisionId: string,
  signal?: AbortSignal,
): Promise<ComisionDetalleResponse> {
  const response = await apiFetch<ComisionDetalleApiResponse>(`/comisiones/${comisionId}`, {
    signal,
  })
  return mapearDetalle(response)
}

/** Asigna un Docente a una comisión (`US-ADJ-25`) — idempotente del lado del backend. */
export async function asignarDocente(
  comisionId: string,
  docenteId: string,
  signal?: AbortSignal,
): Promise<ComisionDetalleResponse> {
  const response = await apiFetch<ComisionDetalleApiResponse>(
    `/comisiones/${comisionId}/docentes`,
    { method: "POST", body: { docente_id: docenteId }, signal },
  )
  return mapearDetalle(response)
}
