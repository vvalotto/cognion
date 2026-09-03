import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate } from "react-router"

import { Logo } from "@/components/Logo"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthBrand } from "@/layouts/AuthLayout"
import { ApiError, apiFetch } from "@/lib/api-client"
import { LoginError } from "@/pages/identidad/LoginError"
import { LoginCuentaBloqueadaError } from "@/pages/identidad/LoginCuentaBloqueadaError"
import { setSession, type Rol } from "@/lib/session"

interface LoginResponse {
  access_token: string
  rol: Rol
  expira_en: string
}

const RUTA_POST_LOGIN: Record<Rol, string> = {
  administrador: "/docentes/nuevo",
  docente: "/",
  estudiante: "/",
}

/** Pantalla de login (§2.1/§2.2 `wireframes-identidad.md`) — consume `POST /identidad/login`. */
export function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(false)
  const [bloqueada, setBloqueada] = useState(false)
  const { setOcultarMarca } = useAuthBrand()

  useEffect(() => {
    setOcultarMarca(bloqueada)
    return () => setOcultarMarca(false)
  }, [bloqueada, setOcultarMarca])

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    const controller = controladorSubmitRef.current
    return () => controller?.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(false)

    try {
      const response = await apiFetch<LoginResponse>("/identidad/login", {
        method: "POST",
        body: { email, password },
        signal: controladorSubmitRef.current?.signal,
      })
      setSession({ token: response.access_token, rol: response.rol })
      void navigate(RUTA_POST_LOGIN[response.rol])
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 403) {
        setBloqueada(true)
        return
      }
      if (err instanceof ApiError) {
        setPassword("")
        setError(true)
        return
      }
      throw err
    }
  }

  return (
    <div>
      {bloqueada ? (
        <div className="mb-2 flex flex-col items-center text-center">
          <Logo size={40} className="mb-2" />
          <h1 className="text-lg font-semibold">Ingresar</h1>
        </div>
      ) : (
        <>
          <h1 className="text-lg font-semibold">Iniciar sesión</h1>
          <p className="mb-4 text-sm text-muted-foreground">Ingresá con tu email y contraseña</p>
        </>
      )}

      {bloqueada ? <LoginCuentaBloqueadaError /> : error && <LoginError />}

      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <fieldset className="flex flex-col gap-3" disabled={bloqueada}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="login-email">Email</Label>
            <Input
              id="login-email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="login-password">Contraseña</Label>
            <Input
              id="login-password"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <Button type="submit">Ingresar</Button>
        </fieldset>
      </form>
    </div>
  )
}
