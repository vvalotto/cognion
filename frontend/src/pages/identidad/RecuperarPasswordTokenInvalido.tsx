import { Link } from "react-router"

import { Button } from "@/components/ui/button"

/**
 * Pantalla "Olvidé mi contraseña" — link vencido/inválido/ya usado (§4.4
 * `wireframes-identidad-autoservicio.md`).
 *
 * No distingue entre `TokenRecuperacionVencido`, `TokenRecuperacionInvalido` y
 * `TokenRecuperacionYaUsado` — mismo mensaje para los tres, mismo criterio que
 * `RegistroError.tsx` (link de invitación vencido/inválido/usado, `wireframes-identidad.md`
 * §2.4). Sin formulario de contraseña — no sugiere que la acción se puede completar igual.
 */
export function RecuperarPasswordTokenInvalido() {
  return (
    <div className="text-center">
      <p className="mb-2 text-4xl" aria-hidden="true">
        ⏱
      </p>
      <h1 className="text-lg font-semibold">Este link ya no es válido</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        El link de recuperación venció, ya fue usado, o no es correcto. Los links valen 1 hora
        y son de un solo uso.
      </p>

      <div
        role="alert"
        className="mt-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-left text-sm text-destructive"
      >
        <span aria-hidden="true">⚠</span>
        <div>
          <p className="font-medium">Link de recuperación vencido o inválido</p>
          <p>Pedí un nuevo link para poder definir tu contraseña.</p>
        </div>
      </div>

      <Button render={<Link to="/recuperar-password" />} className="mt-4 w-full">
        Pedir un nuevo link
      </Button>
    </div>
  )
}
