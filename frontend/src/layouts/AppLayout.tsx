import { Outlet } from "react-router"

import { Logo } from "@/components/Logo"
import { TopStrip } from "@/components/TopStrip"
import { getSession } from "@/lib/session"

/** Layout de las pantallas post-login — header de aplicación con marca + usuario autenticado. */
export function AppLayout() {
  const session = getSession()

  return (
    <div className="min-h-screen bg-background">
      <TopStrip />
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-6 py-3">
        <div className="flex items-center gap-2 text-[15px] font-bold text-primary">
          <Logo size={26} />
          Cognión
        </div>
        {session && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="flex size-7 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">
              {session.rol.slice(0, 2).toUpperCase()}
            </span>
            <span>{session.rol}</span>
          </div>
        )}
      </header>
      <main className="mx-auto max-w-3xl p-6">
        <Outlet />
      </main>
    </div>
  )
}
