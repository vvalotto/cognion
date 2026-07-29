import { Outlet } from "react-router"

import { Logo } from "@/components/Logo"
import { TopStrip } from "@/components/TopStrip"

/** Layout de las pantallas de autenticación — tarjeta centrada, ancho máx. 420px. */
export function AuthLayout() {
  return (
    <div className="min-h-screen bg-muted">
      <TopStrip />
      <div className="flex min-h-[calc(100vh-30px)] items-center justify-center p-4">
        <div className="w-full max-w-[420px] rounded-lg border border-border bg-card p-8 shadow-sm">
          <div className="mb-6 flex flex-col items-center text-center">
            <Logo size={44} className="mb-2" />
            <span className="text-lg font-bold text-primary">Cognión</span>
            <span className="text-sm text-muted-foreground">Evaluación universitaria</span>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
