import { InicioPlaceholder } from "@/pages/_placeholders"
import { HomeDocente } from "@/pages/HomeDocente"
import { getSession } from "@/lib/session"

/**
 * Ruta índice (`/`) — despacha a la home de cada rol (`US-ADJ-28`/`29`/`30`).
 *
 * Estudiante y Administrador siguen en `InicioPlaceholder` hasta que existan sus propias
 * homes (`US-ADJ-29`/`30`).
 */
export function Inicio() {
  const rol = getSession()?.rol

  if (rol === "docente") return <HomeDocente />
  return <InicioPlaceholder />
}
