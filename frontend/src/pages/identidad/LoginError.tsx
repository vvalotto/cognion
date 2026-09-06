/** Alerta de error de login (§2.2 `wireframes-identidad.md`) — mensaje genérico, no distingue si el email existe. */
export function LoginError() {
  return (
    <div
      role="alert"
      className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <p className="font-medium">Email o contraseña incorrectos</p>
      <p>Verificá tus datos e intentá de nuevo.</p>
    </div>
  )
}
