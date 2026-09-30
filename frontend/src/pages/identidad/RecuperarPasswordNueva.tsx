import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { PasswordInput } from "@/components/PasswordInput"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { ApiError } from "@/lib/api-client"
import { confirmarNuevaPassword } from "@/lib/cuentas-api"

/** Distingue el rechazo por política de contraseña del rechazo por token (ver plan de la US:
 * el backend responde 422 con `detail` como string plano, sin código de error propio — las
 * excepciones de política empiezan siempre con este prefijo, `src/identidad/entities/errors.py`). */
function esErrorPoliticaPassword(mensaje: string): boolean {
  return mensaje.startsWith("La contraseña debe")
}

/**
 * Pantalla "Olvidé mi contraseña" — definir nueva contraseña (§4.3
 * `wireframes-identidad-autoservicio.md`) — consume
 * `POST /identidad/recuperar-password/confirmar` (`US-ADJ-39`).
 *
 * Sin campo de "contraseña actual" — a diferencia de `CambiarPassword.tsx`, este flujo no la
 * requiere: quien abrió el link ya demostró control del email vía el token.
 */
export function RecuperarPasswordNueva() {
  const navigate = useNavigate()
  const { token } = useParams<{ token: string }>()

  const [passwordNueva, setPasswordNueva] = useState("")
  const [confirmacion, setConfirmacion] = useState("")
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    // Crea un controller nuevo en cada montaje real — en StrictMode (dev), React monta,
    // desmonta y vuelve a montar el efecto para detectar cleanups faltantes; si el cleanup
    // abortara el mismo controller creado en el render (arriba), el segundo montaje quedaría
    // con la señal ya abortada y todo submit posterior se descartaría en silencio.
    const controller = new AbortController()
    controladorSubmitRef.current = controller
    return () => controller.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (passwordNueva.length < 12) {
      setError("La contraseña nueva debe tener al menos 12 caracteres.")
      return
    }
    if (passwordNueva !== confirmacion) {
      setError("La contraseña y su confirmación no coinciden.")
      return
    }

    try {
      await confirmarNuevaPassword(token ?? "", passwordNueva, controladorSubmitRef.current?.signal)
      if (controladorSubmitRef.current?.signal.aborted) return
      void navigate("/recuperar-password/exito")
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && esErrorPoliticaPassword(err.message)) {
        setError(err.message)
        return
      }
      if (err instanceof ApiError) {
        void navigate("/recuperar-password/invalido")
        return
      }
      throw err
    }
  }

  return (
    <div>
      <h1 className="text-lg font-semibold">Definí tu nueva contraseña</h1>
      <p className="mb-4 text-sm text-muted-foreground">
        Elegí una contraseña nueva para tu cuenta.
      </p>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <Card>
        <CardContent>
          <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="recuperar-password-nueva">Contraseña nueva</Label>
              <PasswordInput
                id="recuperar-password-nueva"
                required
                minLength={12}
                mostrarFortaleza
                value={passwordNueva}
                onChange={(event) => setPasswordNueva(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="recuperar-password-confirmacion">Confirmar contraseña nueva</Label>
              <PasswordInput
                id="recuperar-password-confirmacion"
                required
                minLength={12}
                value={confirmacion}
                onChange={(event) => setConfirmacion(event.target.value)}
              />
            </div>
            <Button type="submit">Guardar nueva contraseña</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
