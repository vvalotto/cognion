import { router } from "@/router"
import { clearSession, getSession } from "@/lib/session"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown
}

/**
 * Cliente HTTP del backend — adjunta el JWT de la sesión (si existe) y traduce las
 * respuestas de error a `ApiError`.
 *
 * Un 401 limpia la sesión guardada y navega a `/login` — ningún caller necesita manejarlo
 * caso por caso. Un 403 se propaga tal cual con el mensaje genérico que ya devuelve el
 * backend (`US-1.1.5`), sin agregar detalle del recurso solicitado.
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

  if (response.status === 401) {
    clearSession()
    void router.navigate("/login")
    throw new ApiError(401, await extractMessage(response))
  }

  if (!response.ok) {
    throw new ApiError(response.status, await extractMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

async function extractMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail
      if (typeof detail === "string") return detail
    }
  } catch {
    // respuesta sin body JSON — se usa el mensaje genérico
  }
  return "Error inesperado."
}
