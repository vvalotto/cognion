interface Props {
  /** `reintentar_en_segundos` del `403 cuenta_bloqueada_temporal` (`US-ADJ-60`). */
  segundos: number
}

/**
 * Alerta de cuenta bloqueada temporalmente en login — pantalla `#login-bloqueada-temporal` del
 * prototipo `identidad-cuentas-administracion.html` (`wireframes-cuentas-administracion.md`
 * §2.11, `US-ADJ-60`). A diferencia del bloqueo permanente, el formulario sigue habilitado.
 */
export function LoginCuentaBloqueadaTemporalError({ segundos }: Props) {
  const minutos = Math.max(1, Math.ceil(segundos / 60))
  return (
    <div
      role="alert"
      className="mb-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
    >
      <span aria-hidden="true">⏳</span>
      <div>
        <p className="font-medium">Cuenta bloqueada temporalmente</p>
        <p>
          Superaste el máximo de intentos. Podés volver a intentar en unos {minutos}{" "}
          {minutos === 1 ? "minuto" : "minutos"}.
        </p>
      </div>
    </div>
  )
}
