import { useLocation, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"

interface AltaDocenteExitoState {
  nombre?: string
  email?: string
}

/**
 * Pantalla de confirmación de alta de Docente (§2.7 `wireframes-identidad.md`).
 *
 * Aclara explícitamente que el Docente todavía no está asignado a ninguna comisión —
 * `AsignarDocenteAComision` es un comando separado, sin UI dedicada en esta iteración.
 */
export function AltaDocenteExito() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as AltaDocenteExitoState | null

  return (
    <div>
      <h1 className="text-lg font-semibold">Docente creado</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {state?.nombre && state?.email
          ? `Se creó la cuenta de ${state.nombre} (${state.email}).`
          : "Se creó la cuenta del Docente."}
      </p>
      <p className="mt-2 text-sm text-muted-foreground">
        Todavía no está asignado a ninguna comisión.
      </p>
      <Button className="mt-4 w-full" onClick={() => navigate("/docentes/nuevo")}>
        Dar de alta otro Docente
      </Button>
    </div>
  )
}
