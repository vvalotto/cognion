import { Outlet } from "react-router"

import { getSession } from "@/lib/session"

/** Layout de las pantallas post-login — header de aplicación con marca + usuario autenticado. */
export function AppLayout() {
  const session = getSession()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border px-6 py-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">Cognion</span>
          {session && (
            <span className="text-sm text-muted-foreground">{session.rol}</span>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-3xl p-6">
        <Outlet />
      </main>
    </div>
  )
}
