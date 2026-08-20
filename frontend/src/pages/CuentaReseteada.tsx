import { useLocation, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"

interface CuentaReseteadaState {
  nombre?: string
}

/** Pantalla de confirmación de reseteo de contraseña (§2.4 `wireframes-cuentas-administracion.md`). */
export function CuentaReseteada() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as CuentaReseteadaState | null

  return (
    <div>
      <h1 className="text-lg font-semibold">Contraseña reseteada</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {state?.nombre
          ? `Se reseteó la contraseña de ${state.nombre} y la cuenta quedó desbloqueada.`
          : "Se reseteó la contraseña y la cuenta quedó desbloqueada."}
      </p>
      <Button className="mt-4 w-full" onClick={() => navigate("/cuentas")}>
        Volver al listado de cuentas
      </Button>
    </div>
  )
}
