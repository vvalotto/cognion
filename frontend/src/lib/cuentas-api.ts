import { apiFetch } from "@/lib/api-client"
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
