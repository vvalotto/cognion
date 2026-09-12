import { Menu } from "@base-ui/react/menu"
import { ChevronDown } from "lucide-react"
import { Link, useNavigate } from "react-router"

import type { Rol } from "@/lib/session"
import { clearSession } from "@/lib/session"

const ETIQUETA_ROL: Record<Rol, string> = {
  docente: "Docente",
  estudiante: "Estudiante",
  administrador: "Administrador",
}

function iniciales(nombre: string): string {
  const partes = nombre.trim().split(/\s+/)
  const primera = partes[0]?.[0] ?? ""
  const ultima = partes.length > 1 ? (partes[partes.length - 1]?.[0] ?? "") : ""
  return (primera + ultima).toUpperCase()
}

interface UserMenuProps {
  nombre: string | null
  rol: Rol
}

/**
 * Menú de usuario (`wireframes-identidad-autoservicio.md` §6) — trigger de avatar/nombre en el
 * header, con "Cambiar contraseña" y "Cerrar sesión" como únicos puntos de entrada por clic a
 * esas dos funciones ya existentes.
 */
export function UserMenu({ nombre, rol }: UserMenuProps) {
  const navigate = useNavigate()
  const etiquetaRol = ETIQUETA_ROL[rol]

  function cerrarSesion() {
    clearSession()
    navigate("/login")
  }

  return (
    <Menu.Root>
      <Menu.Trigger className="flex items-center gap-2 rounded-lg px-1.5 py-1 text-sm text-muted-foreground outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50">
        <span className="flex size-7 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">
          {nombre ? iniciales(nombre) : rol.slice(0, 2).toUpperCase()}
        </span>
        <span className="flex flex-col items-start leading-tight">
          <span className="font-medium text-foreground">{nombre ?? etiquetaRol}</span>
          {nombre && <span className="text-xs">{etiquetaRol}</span>}
        </span>
        <ChevronDown className="size-4 text-muted-foreground" />
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Positioner align="end" sideOffset={6}>
          <Menu.Popup className="min-w-48 rounded-lg border border-border bg-popover py-1 text-sm shadow-md">
            <div className="flex flex-col px-3 py-2">
              <span className="font-medium text-foreground">{nombre ?? etiquetaRol}</span>
              {nombre && <span className="text-xs text-muted-foreground">{etiquetaRol}</span>}
            </div>
            <div className="my-1 h-px bg-border" />
            <Menu.Item
              className="flex cursor-pointer items-center px-3 py-2 text-foreground outline-none data-[highlighted]:bg-muted"
              render={<Link to="/mi-cuenta/cambiar-password" />}
            >
              🔑 Cambiar contraseña
            </Menu.Item>
            <Menu.Item
              className="flex cursor-pointer items-center px-3 py-2 text-destructive outline-none data-[highlighted]:bg-destructive/10"
              onClick={cerrarSesion}
            >
              ↩ Cerrar sesión
            </Menu.Item>
          </Menu.Popup>
        </Menu.Positioner>
      </Menu.Portal>
    </Menu.Root>
  )
}
