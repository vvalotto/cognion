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

export async function listarCuentas(filtros: FiltrosCuentas = {}): Promise<CuentaResponse[]> {
  const params = new URLSearchParams()
  if (filtros.rol) params.set("rol", filtros.rol)
  if (filtros.estado) params.set("estado", filtros.estado)
  if (filtros.busqueda) params.set("busqueda", filtros.busqueda)

  const query = params.toString()
  return apiFetch<CuentaResponse[]>(`/usuarios${query ? `?${query}` : ""}`)
}
