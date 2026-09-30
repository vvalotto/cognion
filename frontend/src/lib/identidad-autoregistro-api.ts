import { apiFetch } from "@/lib/api-client"

export interface UsuarioAutoregistradoResponse {
  id: string
  nombre: string
  email: string
}

interface UsuarioAutoregistradoApiResponse {
  id: string
  nombre: string
  email: string
  tipo_perfil: string
}

function mapearUsuarioAutoregistrado(
  response: UsuarioAutoregistradoApiResponse,
): UsuarioAutoregistradoResponse {
  return { id: response.id, nombre: response.nombre, email: response.email }
}

/** Autoregistra una cuenta de Docente, activa de inmediato (`US-ADJ-41`). Sin JWT. */
export async function autoregistrarDocente(
  nombre: string,
  email: string,
  password: string,
  signal?: AbortSignal,
): Promise<UsuarioAutoregistradoResponse> {
  const response = await apiFetch<UsuarioAutoregistradoApiResponse>(
    "/identidad/autoregistro/docente",
    { method: "POST", body: { nombre, email, password }, signal },
  )
  return mapearUsuarioAutoregistrado(response)
}

/**
 * Autoregistra una cuenta de Estudiante asignada a una comisión, activa de inmediato
 * (`US-ADJ-42`). Sin JWT.
 */
export async function autoregistrarEstudiante(
  nombre: string,
  email: string,
  password: string,
  comisionId: string,
  signal?: AbortSignal,
): Promise<UsuarioAutoregistradoResponse> {
  const response = await apiFetch<UsuarioAutoregistradoApiResponse>(
    "/identidad/autoregistro/estudiante",
    { method: "POST", body: { nombre, email, password, comision_id: comisionId }, signal },
  )
  return mapearUsuarioAutoregistrado(response)
}

export interface MateriaAutoregistroResponse {
  id: string
  nombre: string
}

/**
 * Lista las materias para el selector de la pantalla de autoregistro de Estudiante
 * (`US-ADJ-43`). Endpoint público — quien se autoregistra todavía no tiene JWT, no puede usar
 * `listarMaterias()` de `banco-preguntas-api.ts` (protegido por rol).
 */
export async function listarMateriasAutoregistro(
  signal?: AbortSignal,
): Promise<MateriaAutoregistroResponse[]> {
  return apiFetch<MateriaAutoregistroResponse[]>("/identidad/autoregistro/materias", { signal })
}

export interface ComisionAutoregistroResponse {
  id: string
  horario: string
}

/**
 * Lista las comisiones activas de una materia para el mismo selector (`US-ADJ-43`). Endpoint
 * público — mismo motivo que `listarMateriasAutoregistro`.
 */
export async function listarComisionesAutoregistro(
  materiaId: string,
  signal?: AbortSignal,
): Promise<ComisionAutoregistroResponse[]> {
  return apiFetch<ComisionAutoregistroResponse[]>(
    `/identidad/autoregistro/materias/${materiaId}/comisiones`,
    { signal },
  )
}
