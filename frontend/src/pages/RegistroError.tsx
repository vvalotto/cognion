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
    <div>
      <h1 className="text-lg font-semibold">Este link ya no es válido</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        El link de invitación venció, ya fue usado o no existe. No hay forma de recuperarlo
        automáticamente — pedile a tu docente que te genere uno nuevo.
      </p>
      <Button render={<Link to="/login" />} className="mt-4 w-full">
        Ir a iniciar sesión
      </Button>
    </div>
  )
}
