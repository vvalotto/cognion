import type { ReactNode } from "react"
import { Navigate } from "react-router"

import { getSession, type Rol } from "@/lib/session"

interface RequireRoleProps {
  rol: Rol | Rol[]
  children: ReactNode
}

/**
 * Guard de ruta por rol — sin sesión redirige a `/login`; con sesión pero rol distinto del
 * requerido (o de ninguno de los roles permitidos, si `rol` es un array) muestra un mensaje
 * de acceso denegado en vez de renderizar `children`.
 */
export function RequireRole({ rol, children }: RequireRoleProps) {
  const session = getSession()

  if (!session) {
    return <Navigate to="/login" replace />
  }

  const rolesPermitidos = Array.isArray(rol) ? rol : [rol]
  if (!rolesPermitidos.includes(session.rol)) {
    return (
      <div role="alert" className="text-sm text-destructive">
        <p className="font-medium">Acceso denegado</p>
        <p>No tenés permiso para ver esta pantalla.</p>
      </div>
    )
  }

  return <>{children}</>
}
