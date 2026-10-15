/**
 * Alerta de cuenta deshabilitada en login — pantalla `#login-deshabilitada` del prototipo
 * `identidad-cuentas-administracion.html` (`wireframes-cuentas-administracion.md` §2.9,
 * `US-ADJ-59`). Sin link de recuperación: recuperar la contraseña no reactiva una cuenta dada
 * de baja.
 */
export function LoginCuentaDeshabilitadaError() {
  return (
    <div
      role="alert"
      className="mb-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <span aria-hidden="true">🚫</span>
      <div>
        <p className="font-medium">Cuenta deshabilitada</p>
        <p>Tu cuenta fue dada de baja y no puede iniciar sesión. Contactá a un Administrador.</p>
      </div>
    </div>
  )
}
