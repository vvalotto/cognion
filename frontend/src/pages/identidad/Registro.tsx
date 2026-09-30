import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useNavigate, useSearchParams } from "react-router"

import { PasswordInput } from "@/components/PasswordInput"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError, apiFetch } from "@/lib/api-client"

interface RegistroResponse {
  id: string
  nombre: string
  email: string
  comision_id: string
  materia: string
}

interface InvitacionPreviewResponse {
  materia: string
  horario: string
}

/** Pantalla de registro de Estudiante vía invitación (§2.3 `wireframes-identidad.md`) — consume `POST /identidad/registro`. */
export function Registro() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") ?? ""

  const [nombre, setNombre] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmarPassword, setConfirmarPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<InvitacionPreviewResponse | null>(null)
  const [cargandoPreview, setCargandoPreview] = useState(true)

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

  useEffect(() => {
    // GET de vista previa de la invitación (US-ADJ-08) — controller propio, acotado a la
    // vida de este efecto, sin el problema de StrictMode del efecto anterior porque el
    // fetch y su abort ocurren dentro del mismo montaje.
    const controller = new AbortController()

    async function cargarPreview() {
      try {
        const respuesta = await apiFetch<InvitacionPreviewResponse>(
          `/identidad/invitaciones/${token}`,
          { signal: controller.signal }
        )
        setPreview(respuesta)
        setCargandoPreview(false)
      } catch (err) {
        if (controller.signal.aborted) return
        if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
          void navigate("/registro/error")
          return
        }
        throw err
      }
    }

    void cargarPreview()
    return () => controller.abort()
  }, [token, navigate])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (password.length < 12) {
      setError("La contraseña debe tener al menos 12 caracteres.")
      return
    }
    if (password !== confirmarPassword) {
      setError("Las contraseñas no coinciden.")
      return
    }

    try {
      const response = await apiFetch<RegistroResponse>("/identidad/registro", {
        method: "POST",
        body: { token, nombre, email, password },
        signal: controladorSubmitRef.current?.signal,
      })
      void navigate("/registro/exito", { state: { materia: response.materia } })
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 422) {
        void navigate("/registro/error")
        return
      }
      if (err instanceof ApiError && err.status === 409) {
        setError("Ese email ya está registrado.")
        return
      }
      throw err
    }
  }

  return (
    <div>
      <h1 className="text-lg font-semibold">Crear tu cuenta</h1>
      <p className="mb-4 text-sm text-muted-foreground">Completá tus datos para unirte a la comisión</p>

      {preview && (
        <div className="mb-5 flex w-full items-center gap-1.5 rounded-lg border bg-muted px-3 py-2 text-sm">
          <span className="h-2 w-2 rounded-full bg-green-500" aria-hidden="true" />
          Te vas a unir a <strong>&nbsp;{preview.materia} — {preview.horario}</strong>
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {cargandoPreview ? (
        <p className="text-sm text-muted-foreground">Verificando tu invitación…</p>
      ) : (
        <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="registro-nombre">Nombre completo</Label>
            <Input
              id="registro-nombre"
              type="text"
              required
              value={nombre}
              onChange={(event) => setNombre(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="registro-email">Email</Label>
            <Input
              id="registro-email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="registro-password">Contraseña</Label>
            <PasswordInput
              id="registro-password"
              required
              minLength={12}
              mostrarFortaleza
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="registro-confirmar-password">Confirmar contraseña</Label>
            <PasswordInput
              id="registro-confirmar-password"
              required
              minLength={12}
              value={confirmarPassword}
              onChange={(event) => setConfirmarPassword(event.target.value)}
            />
          </div>
          <Button type="submit">Crear cuenta</Button>
        </form>
      )}

      <p className="mt-4 text-center text-sm text-muted-foreground">
        ¿Ya tenés cuenta?{" "}
        <Link to="/login" className="font-medium text-foreground underline-offset-2 hover:underline">
          Iniciar sesión
        </Link>
      </p>
    </div>
  )
}
