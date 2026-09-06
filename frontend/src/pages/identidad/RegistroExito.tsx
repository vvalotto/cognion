import { Link, useLocation } from "react-router"

import { Button } from "@/components/ui/button"

interface RegistroExitoState {
  materia?: string
}

/**
 * Pantalla de confirmación de registro exitoso (§2.5 `wireframes-identidad.md`).
 *
 * El registro no autentica automáticamente (decisión de simplicidad, sin login automático
 * post-registro en v1) — la acción primaria lleva a `/login`.
 */
export function RegistroExito() {
  const location = useLocation()
  const state = location.state as RegistroExitoState | null
  const materia = state?.materia

  return (
    <div className="text-center">
      <p className="mb-2 text-4xl text-accent" aria-hidden="true">
        ✓
      </p>
      <h1 className="text-lg font-semibold">Cuenta creada</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Ya quedaste asignado a tu comisión. Iniciá sesión para continuar.
      </p>

      {materia && (
        <div className="mt-4 flex gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-left text-sm">
          <span aria-hidden="true">✓</span>
          <div>
            <p className="font-medium text-foreground">{materia}</p>
            <p className="text-muted-foreground">
              Tu cuenta quedó vinculada automáticamente a esta comisión.
            </p>
          </div>
        </div>
      )}

      <Button render={<Link to="/login" />} className="mt-4 w-full">
        Iniciar sesión
      </Button>
    </div>
  )
}
