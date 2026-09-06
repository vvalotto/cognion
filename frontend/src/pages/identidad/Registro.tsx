import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useNavigate, useSearchParams } from "react-router"

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

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.")
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

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
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
          <Input
            id="registro-password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="registro-confirmar-password">Confirmar contraseña</Label>
          <Input
            id="registro-confirmar-password"
            type="password"
            required
            minLength={8}
            value={confirmarPassword}
            onChange={(event) => setConfirmarPassword(event.target.value)}
          />
        </div>
        <Button type="submit">Crear cuenta</Button>
      </form>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        ¿Ya tenés cuenta?{" "}
        <Link to="/login" className="font-medium text-foreground underline-offset-2 hover:underline">
          Iniciar sesión
        </Link>
      </p>
    </div>
  )
}
