import { Link } from "react-router"

import { Button } from "@/components/ui/button"

/**
 * Pantalla de link de invitación inválido/vencido/usado (§2.4 `wireframes-identidad.md`).
 *
 * No distingue entre `InvitacionInvalida`, `InvitacionVencida` e `InvitacionYaUsada` — mismo
 * mensaje y tratamiento para los tres casos (`ADR-012`, coherente con `US-1.1.3`).
 */
export function RegistroError() {
  return (
    <div className="text-center">
      <p className="mb-2 text-4xl" aria-hidden="true">
        ⏱
      </p>
      <h1 className="text-lg font-semibold">Este link ya no es válido</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        El link de invitación venció o no es correcto. No se puede recuperar automáticamente.
      </p>

      <div
        role="alert"
        className="mt-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-left text-sm text-destructive"
      >
        <span aria-hidden="true">⚠</span>
        <div>
          <p className="font-medium">Invitación vencida o inválida</p>
          <p>Pedile a tu docente que te genere un nuevo link de invitación para la comisión.</p>
        </div>
      </div>

      <Button render={<Link to="/login" />} variant="outline" className="mt-4 w-full">
        Ir a iniciar sesión
      </Button>
    </div>
  )
}
