import { Link } from "react-router"

/**
 * Alerta de error de login (§2.2 y §2.2b `wireframes-identidad.md`).
 *
 * El 1.er fallo es genérico y no distingue si el email existe. Desde el 2.º, si el servidor informa
 * `intentosRestantes = 1` (`US-ADJ-69`), avisa que el próximo intento bloquea la cuenta y ofrece
 * recuperar la contraseña por email, que además desbloquea la cuenta (`US-ADJ-62`).
 */
export function LoginError({ intentosRestantes }: { intentosRestantes?: number | null }) {
  return (
    <div
      role="alert"
      className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <p className="font-medium">Email o contraseña incorrectos</p>
      {intentosRestantes === 1 ? (
        <p>
          Te queda 1 intento antes del bloqueo de la cuenta. Si no recordás tu contraseña,{" "}
          <Link to="/recuperar-password" className="font-medium underline underline-offset-2">
            recuperala por email
          </Link>
          .
        </p>
      ) : (
        <p>Verificá tus datos e intentá de nuevo.</p>
      )}
    </div>
  )
}
