import { Link } from "react-router"

import { Button } from "@/components/ui/button"

/**
 * Pantalla de confirmación de autoregistro exitoso (`#autoregistro-exito`,
 * `wireframes-identidad-autoservicio.md` §5.4) — pantalla única para ambos perfiles.
 *
 * Sin login automático post-registro, mismo criterio que `RegistroExito.tsx`.
 */
export function AutoregistroExito() {
  return (
    <div className="text-center">
      <p className="mb-2 text-4xl text-accent" aria-hidden="true">
        ✓
      </p>
      <h1 className="text-lg font-semibold">Cuenta creada</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Tu cuenta ya está activa. Iniciá sesión para continuar.
      </p>

      <Button render={<Link to="/login" />} className="mt-4 w-full">
        Iniciar sesión
      </Button>
    </div>
  )
}
