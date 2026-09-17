import { Link } from "react-router"

import { Button } from "@/components/ui/button"

/**
 * Pantalla "Olvidé mi contraseña" — email enviado (§4.2
 * `wireframes-identidad-autoservicio.md`).
 *
 * Mensaje genérico único — nunca confirma ni niega si el email corresponde a una cuenta
 * (INV-ID-17), mismo criterio que `US-2.2.1`/`US-ADJ-38`.
 */
export function RecuperarPasswordSolicitado() {
  return (
    <div className="text-center">
      <p className="mb-2 text-4xl text-accent" aria-hidden="true">
        ✓
      </p>
      <h1 className="text-lg font-semibold">Revisá tu email</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Si el email ingresado corresponde a una cuenta, te enviamos un link para definir una
        contraseña nueva. El link vale por 1 hora.
      </p>

      <Button render={<Link to="/login" />} className="mt-4 w-full">
        Volver a iniciar sesión
      </Button>
    </div>
  )
}
