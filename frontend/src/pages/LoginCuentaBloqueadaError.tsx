/**
 * Alerta de cuenta bloqueada en login — pantalla `#login-bloqueada` del prototipo
 * `identidad-cuentas-administracion.html` (fuente de verdad UX, no `wireframes-identidad.md`
 * §2.2 como el resto de errores de login).
 */
export function LoginCuentaBloqueadaError() {
  return (
    <div
      role="alert"
      className="mb-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <span aria-hidden="true">🔒</span>
      <div>
        <p className="font-medium">Cuenta bloqueada</p>
        <p>
          Superaste el máximo de intentos permitidos. Contactá a un Administrador para
          restablecer tu contraseña.
        </p>
      </div>
    </div>
  )
}
