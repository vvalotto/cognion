import { Outlet } from "react-router"

import { AppNav } from "@/components/AppNav"
import { Footer } from "@/components/Footer"
import { Logo } from "@/components/Logo"
import { TopStrip } from "@/components/TopStrip"
import { getSession, obtenerNombre } from "@/lib/session"

const ETIQUETA_ROL: Record<string, string> = {
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

/** Layout de las pantallas post-login — header de aplicación con marca + usuario autenticado. */
export function AppLayout() {
  const session = getSession()
  const nombre = session ? obtenerNombre() : null

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <TopStrip />
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-6 py-3">
        <div className="flex items-center gap-2 text-[15px] font-bold text-primary">
          <Logo size={26} />
          Cognión
        </div>
        {session && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="flex size-7 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">
              {nombre ? iniciales(nombre) : session.rol.slice(0, 2).toUpperCase()}
            </span>
            <span className="flex flex-col leading-tight">
              <span className="font-medium text-foreground">{nombre ?? ETIQUETA_ROL[session.rol]}</span>
              {nombre && <span className="text-xs">{ETIQUETA_ROL[session.rol]}</span>}
            </span>
          </div>
        )}
      </header>
      {session && <AppNav rol={session.rol} />}
      <main className="mx-auto w-full max-w-3xl flex-1 p-6">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
