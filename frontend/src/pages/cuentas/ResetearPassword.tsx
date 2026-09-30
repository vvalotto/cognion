import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { PasswordInput } from "@/components/PasswordInput"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { obtenerCuenta, resetearPassword, type CuentaDetalleResponse } from "@/lib/cuentas-api"

/** Pantalla de reseteo de contraseña / desbloqueo (§2.3 `wireframes-cuentas-administracion.md`). */
export function ResetearPassword() {
  const { usuarioId } = useParams<{ usuarioId: string }>()
  const navigate = useNavigate()

  const [cuenta, setCuenta] = useState<CuentaDetalleResponse | null>(null)
  const [passwordNueva, setPasswordNueva] = useState("")
  const [confirmacion, setConfirmacion] = useState("")
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!usuarioId) return undefined
    const controller = new AbortController()
    obtenerCuenta(usuarioId, controller.signal)
      .then((resultado) => setCuenta(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [usuarioId])

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

    if (!usuarioId) return

    if (passwordNueva.length < 12) {
      setError("La contraseña nueva debe tener al menos 12 caracteres.")
      return
    }
    if (passwordNueva !== confirmacion) {
      setError("La contraseña y su confirmación no coinciden.")
      return
    }

    try {
      await resetearPassword(usuarioId, passwordNueva, controladorSubmitRef.current?.signal)
      void navigate(`/cuentas/${usuarioId}/reseteada`, { state: { nombre: cuenta?.nombre } })
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      throw err
    }
  }

  function handleCancelar() {
    void navigate(`/cuentas/${usuarioId}`)
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Administración" },
          { label: "Cuentas", to: "/cuentas" },
          { label: cuenta?.nombre ?? "…", to: usuarioId ? `/cuentas/${usuarioId}` : undefined },
          { label: "Resetear contraseña" },
        ]}
      />
      <h1 className="text-lg font-semibold">Resetear contraseña</h1>
      {cuenta && (
        <p className="text-sm text-muted-foreground">
          {cuenta.nombre} · {cuenta.email}
        </p>
      )}

      <Card className="mt-4">
        <CardContent>
          <div className="flex gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-700 dark:text-amber-400">
            <span aria-hidden="true">ⓘ</span>
            <div>
              <p className="font-medium">Esta acción también desbloquea la cuenta</p>
              <p>
                Si estaba bloqueada por intentos fallidos, queda desbloqueada al fijar la
                nueva contraseña.
              </p>
            </div>
          </div>

          {error && (
            <div
              role="alert"
              className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              <p className="font-medium">{error}</p>
            </div>
          )}

          <form className="mt-4 flex flex-col gap-5" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password-nueva">Nueva contraseña temporal</Label>
              <PasswordInput
                id="password-nueva"
                required
                minLength={12}
                mostrarFortaleza
                value={passwordNueva}
                onChange={(e) => setPasswordNueva(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                El usuario debería cambiarla por una propia (self-service) en su próximo
                ingreso.
              </p>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password-confirmacion">Confirmar contraseña</Label>
              <PasswordInput
                id="password-confirmacion"
                required
                minLength={12}
                value={confirmacion}
                onChange={(e) => setConfirmacion(e.target.value)}
              />
            </div>

            <div className="flex gap-2">
              <Button type="submit" variant="destructive-solid">
                Resetear contraseña
              </Button>
              <Button type="button" variant="outline" onClick={handleCancelar}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
