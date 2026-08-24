import { router } from "@/router"
import { clearSession, getSession } from "@/lib/session"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  status: number
  detail?: unknown

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown
  /**
   * Si es `false`, un 401 no limpia la sesión ni navega a `/login` — se propaga como
   * `ApiError` normal. Uso excepcional: endpoints donde un 401 no significa "sesión
   * inválida" sino un rechazo puntual de la acción (`cambiarPassword`, `US-2.2.8`).
   * Default `true` — no cambia el comportamiento de ningún caller existente.
   */
  handleUnauthorized?: boolean
}

/**
 * Cliente HTTP del backend — adjunta el JWT de la sesión (si existe) y traduce las
 * respuestas de error a `ApiError`.
 *
 * Un 401 limpia la sesión guardada y navega a `/login` — ningún caller necesita manejarlo
 * caso por caso, salvo que pase `handleUnauthorized: false`. Un 403 se propaga tal cual con
 * el mensaje genérico que ya devuelve el backend (`US-1.1.5`), sin agregar detalle del
 * recurso solicitado.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const session = getSession()
  const headers = new Headers(options.headers)
  headers.set("Content-Type", "application/json")
  if (session) {
    headers.set("Authorization", `Bearer ${session.token}`)
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (response.status === 401 && options.handleUnauthorized !== false) {
    clearSession()
    void router.navigate("/login")
    const { message } = await extractError(response)
    throw new ApiError(401, message)
  }

  if (!response.ok) {
    const { message, detail } = await extractError(response)
    throw new ApiError(response.status, message, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

interface ExtractedError {
  message: string
  detail?: unknown
}

async function extractError(response: Response): Promise<ExtractedError> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail
      if (typeof detail === "string") return { message: detail }
      if (detail && typeof detail === "object" && "mensaje" in detail) {
        const mensaje = (detail as { mensaje: unknown }).mensaje
        if (typeof mensaje === "string") return { message: mensaje, detail }
      }
    }
  } catch {
    // respuesta sin body JSON — se usa el mensaje genérico
  }
  return { message: "Error inesperado." }
}
