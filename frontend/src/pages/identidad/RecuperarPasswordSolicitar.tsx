import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { solicitarRecuperacionPassword } from "@/lib/cuentas-api"

/**
 * Pantalla "Olvidé mi contraseña" — solicitar (§4.1 `wireframes-identidad-autoservicio.md`) —
 * consume `POST /identidad/recuperar-password/solicitar` (`US-ADJ-38`).
 *
 * Cualquier email envía siempre a la misma pantalla de confirmación genérica (INV-ID-17) — no
 * hay caso de negocio que distinguir en la respuesta 202.
 */
export function RecuperarPasswordSolicitar() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")

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
    await solicitarRecuperacionPassword(email, controladorSubmitRef.current?.signal)
    if (controladorSubmitRef.current?.signal.aborted) return
    void navigate("/recuperar-password/solicitado")
  }

  return (
    <div>
      <h1 className="text-lg font-semibold">¿Olvidaste tu contraseña?</h1>
      <p className="mb-4 text-sm text-muted-foreground">
        Ingresá tu email y te enviamos un link para definir una contraseña nueva.
      </p>

      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="recuperar-email">Email</Label>
          <Input
            id="recuperar-email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <Button type="submit">Enviar link de recuperación</Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        <Link to="/login" className="font-medium text-foreground underline-offset-2 hover:underline">
          ‹ Volver a iniciar sesión
        </Link>
      </p>
    </div>
  )
}
