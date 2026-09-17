import { Outlet } from "react-router"

import { AppNav } from "@/components/AppNav"
import { Footer } from "@/components/Footer"
import { Logo } from "@/components/Logo"
import { TopStrip } from "@/components/TopStrip"
import { UserMenu } from "@/components/UserMenu"
import { getSession, obtenerNombre } from "@/lib/session"

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
        {session && <UserMenu nombre={nombre} rol={session.rol} />}
      </header>
      {session && <AppNav rol={session.rol} />}
      <main className="mx-auto w-full max-w-3xl flex-1 p-6">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
