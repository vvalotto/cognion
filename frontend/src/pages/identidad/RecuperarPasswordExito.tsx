import { Link } from "react-router"

import { Button } from "@/components/ui/button"

/**
 * Pantalla "Olvidé mi contraseña" — éxito (§4.5 `wireframes-identidad-autoservicio.md`),
 * evento `PasswordRecuperada`.
 */
export function RecuperarPasswordExito() {
  return (
    <div className="text-center">
      <p className="mb-2 text-4xl text-accent" aria-hidden="true">
        ✓
      </p>
      <h1 className="text-lg font-semibold">Contraseña actualizada</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Ya podés iniciar sesión con tu nueva contraseña.
      </p>

      <Button render={<Link to="/login" />} className="mt-4 w-full">
        Iniciar sesión
      </Button>
    </div>
  )
}
