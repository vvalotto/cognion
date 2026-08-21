import { ApiError, apiFetch } from "@/lib/api-client"
import type { Rol } from "@/lib/session"

export type Estado = "activa" | "bloqueada"

export interface CuentaResponse {
  id: string
  nombre: string
  email: string
  perfil: Rol
  bloqueada: boolean
}

export interface FiltrosCuentas {
  rol?: Rol
  estado?: Estado
  busqueda?: string
}

export interface CuentaDetalleResponse extends CuentaResponse {
  creadoEn: string
  comisionId: string | null
}

interface CuentaDetalleApiResponse {
  id: string
  nombre: string
  email: string
  perfil: Rol
  bloqueada: boolean
  creado_en: string
  comision_id: string | null
}

export async function listarCuentas(filtros: FiltrosCuentas = {}): Promise<CuentaResponse[]> {
  const params = new URLSearchParams()
  if (filtros.rol) params.set("rol", filtros.rol)
  if (filtros.estado) params.set("estado", filtros.estado)
  if (filtros.busqueda) params.set("busqueda", filtros.busqueda)

  const query = params.toString()
  return apiFetch<CuentaResponse[]>(`/usuarios${query ? `?${query}` : ""}`)
}

function aCuentaDetalleResponse(datos: CuentaDetalleApiResponse): CuentaDetalleResponse {
  return {
    id: datos.id,
    nombre: datos.nombre,
    email: datos.email,
    perfil: datos.perfil,
    bloqueada: datos.bloqueada,
    creadoEn: datos.creado_en,
    comisionId: datos.comision_id,
  }
}

export async function obtenerCuenta(id: string): Promise<CuentaDetalleResponse> {
  const datos = await apiFetch<CuentaDetalleApiResponse>(`/usuarios/${id}`)
  return aCuentaDetalleResponse(datos)
}

export async function resetearPassword(
  id: string,
  passwordNueva: string,
): Promise<CuentaDetalleResponse> {
  const datos = await apiFetch<CuentaDetalleApiResponse>(`/usuarios/${id}/resetear-password`, {
    method: "POST",
    body: { password_nueva: passwordNueva },
  })
  return aCuentaDetalleResponse(datos)
}

interface CambiarPasswordErrorDetail {
  mensaje: string
  intentos_restantes?: number
  bloqueada?: boolean
}

/** Error de `cambiarPassword` con los datos que la UI necesita para el mensaje (`US-2.2.8`). */
export class CambiarPasswordError extends Error {
  intentosRestantes?: number
  bloqueada: boolean

  constructor(mensaje: string, intentosRestantes: number | undefined, bloqueada: boolean) {
    super(mensaje)
    this.name = "CambiarPasswordError"
    this.intentosRestantes = intentosRestantes
    this.bloqueada = bloqueada
  }
}

function esDetalleCambiarPassword(detail: unknown): detail is CambiarPasswordErrorDetail {
  return typeof detail === "object" && detail !== null && "mensaje" in detail
}

/**
 * Cambia la contraseña del Usuario autenticado (`PUT /usuarios/me/password`, `US-2.2.5`).
 *
 * Usa `handleUnauthorized: false` porque un 401 acá es un rechazo puntual de la acción
 * (contraseña actual incorrecta), no una sesión inválida — el interceptor global de
 * `apiFetch` no debe desloguear al usuario en este flujo.
 */
export async function cambiarPassword(
  passwordActual: string,
  passwordNueva: string,
): Promise<void> {
  try {
    await apiFetch<void>("/usuarios/me/password", {
      method: "PUT",
      body: { password_actual: passwordActual, password_nueva: passwordNueva },
      handleUnauthorized: false,
    })
  } catch (err) {
    if (err instanceof ApiError && esDetalleCambiarPassword(err.detail)) {
      throw new CambiarPasswordError(
        err.detail.mensaje,
        err.detail.intentos_restantes,
        err.detail.bloqueada ?? false,
      )
    }
    throw err
  }
}
