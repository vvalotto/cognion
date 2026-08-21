/** Alerta de cuenta bloqueada en login (§2.8 `wireframes-cuentas-administracion.md`) — extiende `LoginError.tsx`. */
export function LoginCuentaBloqueadaError() {
  return (
    <div
      role="alert"
      className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <p className="font-medium">Cuenta bloqueada</p>
      <p>Contactá a un Administrador para desbloquearla.</p>
    </div>
  )
}
