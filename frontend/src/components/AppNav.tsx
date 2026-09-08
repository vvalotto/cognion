import { Link, useLocation } from "react-router"

import type { Rol } from "@/lib/session"

interface ItemNav {
  label: string
  to: string
}

const ITEMS_POR_ROL: Record<Rol, ItemNav[]> = {
  docente: [
    { label: "Inicio", to: "/" },
    { label: "Banco de Preguntas", to: "/materias" },
    { label: "Actividades", to: "/actividad-evaluativa/materias" },
    { label: "Desempeño por alumno", to: "/analytics/desempeno-por-alumno" },
    { label: "Desempeño por tema", to: "/analytics/desempeno-por-tema" },
  ],
  estudiante: [
    { label: "Inicio", to: "/" },
    { label: "Mis Actividades", to: "/mis-actividades/materias" },
    { label: "Mi Desempeño", to: "/analytics/mi-desempeno" },
  ],
  administrador: [
    { label: "Inicio", to: "/" },
    { label: "Materias", to: "/materias" },
    { label: "Comisiones", to: "/comisiones" },
    { label: "Cuentas", to: "/cuentas" },
  ],
}

function esItemActivo(pathname: string, to: string): boolean {
  if (to === "/") return pathname === "/"
  return pathname === to || pathname.startsWith(`${to}/`)
}

/**
 * Menú de navegación persistente (`.app-nav`, `wireframes-portal-entrada.md` §2.4) — ítems
 * condicionados por rol, visible en toda pantalla post-login (`AppLayout.tsx`).
 */
export function AppNav({ rol }: { rol: Rol }) {
  const { pathname } = useLocation()
  const items = ITEMS_POR_ROL[rol]

  return (
    <nav className="flex flex-wrap gap-1 border-b border-border bg-card px-6">
      {items.map((item) => {
        const activo = esItemActivo(pathname, item.to)
        return (
          <Link
            key={item.to}
            to={item.to}
            aria-current={activo ? "page" : undefined}
            className={
              activo
                ? "border-b-2 border-primary px-3.5 py-3 text-[13px] font-bold text-primary"
                : "border-b-2 border-transparent px-3.5 py-3 text-[13px] font-medium text-muted-foreground hover:text-foreground"
            }
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}
