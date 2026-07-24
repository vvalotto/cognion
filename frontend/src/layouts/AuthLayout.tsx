import { Outlet } from "react-router"

/** Layout de las pantallas de autenticación — tarjeta centrada, ancho máx. 420px. */
export function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-[420px] rounded-lg border border-border bg-card p-6 shadow-sm">
        <Outlet />
      </div>
    </div>
  )
}
