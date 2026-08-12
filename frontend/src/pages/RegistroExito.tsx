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
    <div>
      <h1 className="text-lg font-semibold">Cuenta creada</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {materia
          ? `Ya quedaste asignado automáticamente a tu comisión de ${materia}.`
          : "Ya quedaste asignado automáticamente a tu comisión."}
      </p>
      <Button render={<Link to="/login" />} className="mt-4 w-full">
        Iniciar sesión
      </Button>
    </div>
  )
}
