const STORAGE_KEY = "cognion.session"

export type Rol = "administrador" | "docente" | "estudiante"

export interface Session {
  token: string
  rol: Rol
}

export function getSession(): Session | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as Session
  } catch {
    return null
  }
}

export function setSession(session: Session): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEY)
}

/**
 * Decodifica el claim `sub` (id de usuario) del JWT de la sesión actual.
 *
 * No verifica la firma — el backend ya la valida en cada request; el cliente solo necesita
 * leer el payload para completar campos como `administrador_id` en formularios (`US-ADJ-24`).
 */
export function obtenerUsuarioId(): string | null {
  const session = getSession()
  if (!session) return null

  const partes = session.token.split(".")
  if (partes.length !== 3) return null

  try {
    const payloadBase64 = partes[1].replace(/-/g, "+").replace(/_/g, "/")
    const payloadJson = decodeURIComponent(
      atob(payloadBase64)
        .split("")
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join(""),
    )
    const payload = JSON.parse(payloadJson) as { sub?: string }
    return payload.sub ?? null
  } catch {
    return null
  }
}
