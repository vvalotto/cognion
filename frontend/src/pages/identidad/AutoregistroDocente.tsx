import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { PasswordInput } from "@/components/PasswordInput"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError } from "@/lib/api-client"
import { autoregistrarDocente } from "@/lib/identidad-autoregistro-api"

/**
 * Pantalla de autoregistro de Docente (`#autoregistro-docente`,
 * `wireframes-identidad-autoservicio.md` §5.2) — consume `POST /identidad/autoregistro/docente`
 * (`US-ADJ-41`). Cuenta activa de inmediato, sin aprobación ni verificación de email
 * (INV-ID-16).
 */
export function AutoregistroDocente() {
  const navigate = useNavigate()

  const [nombre, setNombre] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmarPassword, setConfirmarPassword] = useState("")
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

    if (password !== confirmarPassword) {
      setError("Las contraseñas no coinciden.")
      return
    }

    try {
      await autoregistrarDocente(nombre, email, password, controladorSubmitRef.current?.signal)
      void navigate("/autoregistro/exito")
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && (err.status === 409 || err.status === 422)) {
        setError(err.message)
        return
      }
      throw err
    }
  }

  return (
    <div>
      <p className="mb-2 inline-block rounded-full bg-muted px-2.5 py-1 text-xs font-medium">
        🧑‍🏫 Perfil: Docente
      </p>
      <h1 className="text-lg font-semibold">Creá tu cuenta de Docente</h1>
      <p className="mb-4 text-sm text-muted-foreground">Tu cuenta queda activa de inmediato</p>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-docente-nombre">Nombre completo</Label>
          <Input
            id="autoregistro-docente-nombre"
            type="text"
            required
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-docente-email">Email</Label>
          <Input
            id="autoregistro-docente-email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-docente-password">Contraseña</Label>
          <PasswordInput
            id="autoregistro-docente-password"
            required
            minLength={12}
            mostrarFortaleza
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="autoregistro-docente-confirmar-password">Confirmar contraseña</Label>
          <PasswordInput
            id="autoregistro-docente-confirmar-password"
            required
            minLength={12}
            value={confirmarPassword}
            onChange={(event) => setConfirmarPassword(event.target.value)}
          />
        </div>
        <Button type="submit">Crear cuenta</Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        <Link
          to="/autoregistro"
          className="font-medium text-foreground underline-offset-2 hover:underline"
        >
          ‹ Elegir otro perfil
        </Link>
      </p>
    </div>
  )
}
