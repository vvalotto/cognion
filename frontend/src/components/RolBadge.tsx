import { Badge } from "@/components/ui/badge"
import type { Rol } from "@/lib/session"

const ETIQUETA_ROL: Record<Rol, string> = {
  administrador: "Administrador",
  docente: "Docente",
  estudiante: "Estudiante",
}

const VARIANTE_ROL: Record<Rol, "rol-docente" | "rol-estudiante" | "rol-admin"> = {
  docente: "rol-docente",
  estudiante: "rol-estudiante",
  administrador: "rol-admin",
}

/** Badge de rol de usuario — antes duplicado idéntico en `Cuentas.tsx`/`CuentaDetalle.tsx`. */
export function RolBadge({ rol }: { rol: Rol }) {
  return <Badge variant={VARIANTE_ROL[rol]}>{ETIQUETA_ROL[rol]}</Badge>
}
