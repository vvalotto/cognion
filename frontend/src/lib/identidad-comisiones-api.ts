import { apiFetch } from "@/lib/api-client"
import { obtenerUsuarioId } from "@/lib/session"

export interface ComisionResumenResponse {
  id: string
  horario: string
  docentesAsignados: string[]
  activa: boolean
}

interface ComisionResumenApiResponse {
  id: string
  horario: string
  docentes_asignados: string[]
  activa: boolean
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
/**
 * Lista las comisiones activas de una materia; con `incluirInactivas: true` también trae
 * las deshabilitadas — lo usa la pantalla de gestión de Comisiones, que permite
 * reactivarlas.
 */
export async function listarComisionesPorMateria(
  materiaId: string,
  signal?: AbortSignal,
  incluirInactivas = false,
): Promise<ComisionResumenResponse[]> {
  const query = incluirInactivas ? "?incluir_inactivas=true" : ""
  const response = await apiFetch<ComisionResumenApiResponse[]>(
    `/materias/${materiaId}/comisiones${query}`,
    { signal },
  )
  return response.map((comision) => ({
    id: comision.id,
    horario: comision.horario,
    docentesAsignados: comision.docentes_asignados,
    activa: comision.activa,
  }))
}

/** Reactiva una comisión deshabilitada. */
export async function activarComision(
  comisionId: string,
  signal?: AbortSignal,
): Promise<ComisionDetalleResponse> {
  const response = await apiFetch<ComisionDetalleApiResponse>(
    `/comisiones/${comisionId}/activar`,
    { method: "POST", signal },
  )
  return mapearDetalle(response)
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
  materiaId: string
  horario: string
  docentesAsignados: string[]
  activa: boolean
}

interface ComisionDetalleApiResponse {
  id: string
  materia_id: string
  horario: string
  administrador_id: string
  docentes_asignados: string[]
  activa: boolean
}

function mapearDetalle(response: ComisionDetalleApiResponse): ComisionDetalleResponse {
  return {
    id: response.id,
    materiaId: response.materia_id,
    horario: response.horario,
    activa: response.activa,
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

/** Corrige el horario de una comisión existente. */
/**
 * Elimina una comisión, o la deshabilita si tiene estudiantes inscriptos (respuesta 200 en
 * ese caso; 204 sin cuerpo si se borró físicamente — de cualquier forma, deja de aparecer
 * en el listado).
 */
export async function eliminarComision(comisionId: string, signal?: AbortSignal): Promise<void> {
  await apiFetch<void>(`/comisiones/${comisionId}`, { method: "DELETE", signal })
}

export async function editarComision(
  comisionId: string,
  horario: string,
  signal?: AbortSignal,
): Promise<ComisionDetalleResponse> {
  const response = await apiFetch<ComisionDetalleApiResponse>(`/comisiones/${comisionId}`, {
    method: "PATCH",
    body: { horario },
    signal,
  })
  return mapearDetalle(response)
}

export interface InvitacionResponse {
  id: string
  comisionId: string
  docenteId: string
  expiraEn: string
  token: string
}

interface InvitacionApiResponse {
  id: string
  comision_id: string
  docente_id: string
  expira_en: string
  token: string
}

/**
 * Genera una invitación para que el Docente comparta el link manualmente (`US-ADJ-26`) — sin
 * `email_destinatario`, el backend omite el envío de email y solo devuelve el `token`.
 */
export async function generarInvitacion(
  comisionId: string,
  docenteId: string,
  signal?: AbortSignal,
): Promise<InvitacionResponse> {
  const response = await apiFetch<InvitacionApiResponse>(
    `/comisiones/${comisionId}/invitaciones`,
    { method: "POST", body: { docente_id: docenteId }, signal },
  )
  return {
    id: response.id,
    comisionId: response.comision_id,
    docenteId: response.docente_id,
    expiraEn: response.expira_en,
    token: response.token,
  }
}

/** Duraciones elegibles de un link grupal, en minutos (`US-ADJ-67`); la de 1 hora es la de por defecto. */
export const DURACIONES_INVITACION_GRUPAL = [
  { minutos: 15, etiqueta: "15 minutos" },
  { minutos: 60, etiqueta: "1 hora" },
  { minutos: 1440, etiqueta: "1 día" },
] as const

export const DURACION_INVITACION_GRUPAL_POR_DEFECTO = 60

export type EstadoInvitacionGrupal = "vigente" | "vencida" | "revocada"

export interface InvitacionGrupalEstado {
  id: string
  estado: EstadoInvitacionGrupal
  /** Solo viaja mientras el link está vigente. */
  token: string | null
  generadaEn: string
  expiraEn: string
  usos: number
}

interface InvitacionGrupalEstadoApiResponse {
  id: string
  estado: EstadoInvitacionGrupal
  token: string | null
  generada_en: string
  expira_en: string
  usos: number
}

interface InvitacionGrupalApiResponse {
  id: string
  comision_id: string
  expira_en: string
  token: string
}

function mapearEstadoInvitacionGrupal(r: InvitacionGrupalEstadoApiResponse): InvitacionGrupalEstado {
  return {
    id: r.id,
    estado: r.estado,
    token: r.token,
    generadaEn: r.generada_en,
    expiraEn: r.expira_en,
    usos: r.usos,
  }
}

/** Genera el link grupal de la comisión y desactiva el vigente anterior (`US-ADJ-67`). */
export async function generarInvitacionGrupal(
  comisionId: string,
  duracionMinutos: number,
  signal?: AbortSignal,
): Promise<InvitacionGrupalEstado> {
  const response = await apiFetch<InvitacionGrupalApiResponse>(
    `/comisiones/${comisionId}/invitaciones-grupales`,
    { method: "POST", body: { duracion_minutos: duracionMinutos }, signal },
  )
  return {
    id: response.id,
    estado: "vigente",
    token: response.token,
    generadaEn: new Date().toISOString(),
    expiraEn: response.expira_en,
    usos: 0,
  }
}

/** Último link grupal de la comisión, o `null` si nunca generó uno (`US-ADJ-67`). */
export async function obtenerUltimaInvitacionGrupal(
  comisionId: string,
  signal?: AbortSignal,
): Promise<InvitacionGrupalEstado | null> {
  const response = await apiFetch<InvitacionGrupalEstadoApiResponse | null>(
    `/comisiones/${comisionId}/invitaciones-grupales/ultima`,
    { signal },
  )
  return response === null ? null : mapearEstadoInvitacionGrupal(response)
}

/** Desactiva el link grupal; quienes ya se registraron no se ven afectados (`US-ADJ-67`). */
export async function desactivarInvitacionGrupal(
  comisionId: string,
  invitacionId: string,
  signal?: AbortSignal,
): Promise<void> {
  await apiFetch<void>(
    `/comisiones/${comisionId}/invitaciones-grupales/${invitacionId}/revocar`,
    { method: "POST", signal },
  )
}
