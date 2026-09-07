import { InicioPlaceholder } from "@/pages/_placeholders"
import { HomeDocente } from "@/pages/HomeDocente"
import { HomeEstudiante } from "@/pages/HomeEstudiante"
import { getSession } from "@/lib/session"

/**
 * Ruta índice (`/`) — despacha a la home de cada rol (`US-ADJ-28`/`29`/`30`).
 *
 * Administrador sigue en `InicioPlaceholder` hasta que exista su propia home (`US-ADJ-30`).
 */
export function Inicio() {
  const rol = getSession()?.rol

  if (rol === "docente") return <HomeDocente />
  if (rol === "estudiante") return <HomeEstudiante />
  return <InicioPlaceholder />
}
