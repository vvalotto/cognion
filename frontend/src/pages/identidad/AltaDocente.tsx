import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError, apiFetch } from "@/lib/api-client"

interface UsuarioResponse {
  id: string
  nombre: string
  email: string
  perfil: string
}

/** Pantalla de alta de Docente (§2.6 `wireframes-identidad.md`) — consume `POST /usuarios`. */
export function AltaDocente() {
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

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.")
      return
    }
    if (password !== confirmarPassword) {
      setError("Las contraseñas no coinciden.")
      return
    }

    try {
      const response = await apiFetch<UsuarioResponse>("/usuarios", {
        method: "POST",
        body: { nombre, email, password, perfil: "docente" },
        signal: controladorSubmitRef.current?.signal,
      })
      void navigate("/docentes/nuevo/exito", {
        state: { nombre: response.nombre, email: response.email },
      })
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 409) {
        setError("Ese email ya está registrado.")
        return
      }
      throw err
    }
  }

  return (
    <div>
      <p className="text-sm text-muted-foreground">Cuentas › Nuevo Docente</p>
      <h1 className="text-lg font-semibold">Crear cuenta de Docente</h1>
      <p className="mb-4 text-sm text-muted-foreground">
        La contraseña es temporal — el Docente la usa para generar invitaciones.
      </p>

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
          <Label>Perfil</Label>
          <p className="text-sm text-muted-foreground">Docente</p>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="alta-docente-nombre">Nombre completo</Label>
          <Input
            id="alta-docente-nombre"
            type="text"
            required
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="alta-docente-email">Email</Label>
          <Input
            id="alta-docente-email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="alta-docente-password">Contraseña temporal</Label>
          <Input
            id="alta-docente-password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="alta-docente-confirmar-password">Confirmar contraseña</Label>
          <Input
            id="alta-docente-confirmar-password"
            type="password"
            required
            minLength={8}
            value={confirmarPassword}
            onChange={(event) => setConfirmarPassword(event.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button type="submit">Crear cuenta de Docente</Button>
          <Button type="button" variant="outline" onClick={() => navigate("/")}>
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  )
}
