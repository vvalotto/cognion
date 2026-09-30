import { Navigate } from "react-router"

import { InicioPlaceholder } from "@/pages/_placeholders"
import { HomeAdministrador } from "@/pages/HomeAdministrador"
import { HomeDocente } from "@/pages/HomeDocente"
import { HomeEstudiante } from "@/pages/HomeEstudiante"
import { getSession } from "@/lib/session"

/**
 * Ruta índice (`/`) — despacha a la home de cada rol (`US-ADJ-28`/`29`/`30`).
 *
 * A diferencia de las demás rutas post-login, `/` no está envuelta en `RequireRole` (no
 * exige un rol específico) — por eso repite acá su chequeo de sesión: sin sesión, redirige a
 * `/login` en vez de renderizar `InicioPlaceholder`. Ese placeholder queda como fallback
 * defensivo solo para el caso de sesión presente con `rol` no reconocido (no debería ocurrir).
 */
export function Inicio() {
  const session = getSession()

  if (!session) return <Navigate to="/login" replace />
  if (session.rol === "docente") return <HomeDocente />
  if (session.rol === "estudiante") return <HomeEstudiante />
  if (session.rol === "administrador") return <HomeAdministrador />
  return <InicioPlaceholder />
}
