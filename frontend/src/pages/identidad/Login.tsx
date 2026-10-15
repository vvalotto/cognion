import { useEffect, useRef, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router"

import { Logo } from "@/components/Logo"
import { PasswordInput } from "@/components/PasswordInput"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthBrand } from "@/layouts/AuthLayout"
import { ApiError, apiFetch } from "@/lib/api-client"
import { LoginError } from "@/pages/identidad/LoginError"
import { LoginCuentaBloqueadaError } from "@/pages/identidad/LoginCuentaBloqueadaError"
import { LoginCuentaBloqueadaTemporalError } from "@/pages/identidad/LoginCuentaBloqueadaTemporalError"
import { LoginCuentaDeshabilitadaError } from "@/pages/identidad/LoginCuentaDeshabilitadaError"
import { setSession, type Rol } from "@/lib/session"

interface LoginResponse {
  access_token: string
  rol: Rol
  expira_en: string
}

/** El `403` de cuenta deshabilitada trae `detail.codigo`; el de bloqueada, texto plano (`US-ADJ-59`). */
function esCuentaDeshabilitada(detail: unknown): boolean {
  return (
    typeof detail === "object" &&
    detail !== null &&
    "codigo" in detail &&
    (detail as { codigo: unknown }).codigo === "cuenta_deshabilitada"
  )
}

/** El `403` de bloqueo temporal trae `reintentar_en_segundos` (`US-ADJ-60`); `null` si no aplica. */
function segundosDeBloqueoTemporal(detail: unknown): number | null {
  if (typeof detail !== "object" || detail === null) return null
  const { codigo, reintentar_en_segundos } = detail as Record<string, unknown>
  if (codigo !== "cuenta_bloqueada_temporal") return null
  return typeof reintentar_en_segundos === "number" ? reintentar_en_segundos : 1
}

/** Pantalla de login (§2.1/§2.2 `wireframes-identidad.md`) — consume `POST /identidad/login`. */
export function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(false)
  const [bloqueo, setBloqueo] = useState<"bloqueada" | "deshabilitada" | null>(null)
  const [segundosTemporal, setSegundosTemporal] = useState<number | null>(null)
  const bloqueada = bloqueo !== null
  const { setOcultarMarca } = useAuthBrand()

  useEffect(() => {
    setOcultarMarca(bloqueada)
    return () => setOcultarMarca(false)
  }, [bloqueada, setOcultarMarca])

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
    setError(false)
    setSegundosTemporal(null)

    try {
      const response = await apiFetch<LoginResponse>("/identidad/login", {
        method: "POST",
        body: { email, password },
        signal: controladorSubmitRef.current?.signal,
      })
      setSession({ token: response.access_token, rol: response.rol })
      void navigate("/")
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 403) {
        const segundos = segundosDeBloqueoTemporal(err.detail)
        if (segundos !== null) {
          setPassword("")
          setSegundosTemporal(segundos)
          return
        }
        setBloqueo(esCuentaDeshabilitada(err.detail) ? "deshabilitada" : "bloqueada")
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

      {bloqueo === "deshabilitada" && <LoginCuentaDeshabilitadaError />}
      {bloqueo === "bloqueada" && <LoginCuentaBloqueadaError />}
      {segundosTemporal !== null && <LoginCuentaBloqueadaTemporalError segundos={segundosTemporal} />}
      {bloqueo === null && error && <LoginError />}

      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
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
            <PasswordInput
              id="login-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <div className="flex items-center justify-end">
            <Link
              to="/recuperar-password"
              className="text-sm font-medium text-muted-foreground underline-offset-2 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <Button type="submit">Ingresar</Button>
        </fieldset>
      </form>

      {!bloqueada && (
        <p className="mt-4 text-center text-sm text-muted-foreground">
          ¿No tenés cuenta?{" "}
          <Link to="/autoregistro" className="font-medium text-foreground underline-offset-2 hover:underline">
            Registrate
          </Link>
        </p>
      )}
    </div>
  )
}
