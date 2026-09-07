import { InicioPlaceholder } from "@/pages/_placeholders"
import { HomeAdministrador } from "@/pages/HomeAdministrador"
import { HomeDocente } from "@/pages/HomeDocente"
import { HomeEstudiante } from "@/pages/HomeEstudiante"
import { getSession } from "@/lib/session"

/**
 * Ruta índice (`/`) — despacha a la home de cada rol (`US-ADJ-28`/`29`/`30`).
 *
 * `InicioPlaceholder` queda como fallback defensivo si `rol` no está definido (no debería
 * ocurrir en un usuario autenticado — `AppLayout` solo se monta con sesión).
 */
export function Inicio() {
  const rol = getSession()?.rol

  if (rol === "docente") return <HomeDocente />
  if (rol === "estudiante") return <HomeEstudiante />
  if (rol === "administrador") return <HomeAdministrador />
  return <InicioPlaceholder />
}
