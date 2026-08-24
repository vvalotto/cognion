import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CambiarPasswordError, cambiarPassword } from "@/lib/cuentas-api"

type Estado = "formulario" | "exito"

/**
 * Pantalla "Cambiar mi contraseña" (§2.5-§2.7 `wireframes-cuentas-administracion.md`).
 *
 * Un único componente cubre los tres estados del wireframe (formulario, error, éxito) — el
 * error se muestra como alerta sobre el propio formulario, sin ruta separada.
 */
export function CambiarPassword() {
  const navigate = useNavigate()

  const [estado, setEstado] = useState<Estado>("formulario")
  const [passwordActual, setPasswordActual] = useState("")
  const [passwordNueva, setPasswordNueva] = useState("")
  const [confirmacion, setConfirmacion] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [bloqueada, setBloqueada] = useState(false)

  function limpiarCampos() {
    setPasswordActual("")
    setPasswordNueva("")
    setConfirmacion("")
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (passwordNueva.length < 8) {
      setError("La contraseña nueva debe tener al menos 8 caracteres.")
      return
    }
    if (passwordNueva !== confirmacion) {
      setError("La contraseña y su confirmación no coinciden.")
      return
    }

    try {
      await cambiarPassword(passwordActual, passwordNueva)
      setEstado("exito")
    } catch (err) {
      if (err instanceof CambiarPasswordError) {
        if (err.bloqueada) {
          setBloqueada(true)
          setError("Tu cuenta quedó bloqueada. Contactá a un Administrador para reactivarla.")
        } else {
          const restantes = err.intentosRestantes
          setError(
            restantes !== undefined
              ? `Contraseña actual incorrecta. Intentos restantes antes del bloqueo: ${restantes}.`
              : "Contraseña actual incorrecta.",
          )
        }
        limpiarCampos()
        return
      }
      throw err
    }
  }

  if (estado === "exito") {
    return (
      <div className="mx-auto mt-16 max-w-md">
        <Card className="p-8 text-center">
          <p className="mb-2 text-4xl text-accent">✓</p>
          <h1 className="text-lg font-semibold">Contraseña actualizada</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Tu contraseña se cambió correctamente. No hizo falta volver a iniciar sesión — tu
            sesión actual sigue activa.
          </p>
          <Button className="mt-4 w-full" onClick={() => navigate(-1)}>
            Continuar
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <Breadcrumb items={[{ label: "Mi cuenta" }, { label: "Cambiar contraseña" }]} />
      <h1 className="text-lg font-semibold">Cambiar mi contraseña</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Tu sesión actual sigue activa mientras completás este formulario.
      </p>

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <Card className="mt-4">
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password-actual">Contraseña actual</Label>
              <Input
                id="password-actual"
                type="password"
                required
                disabled={bloqueada}
                value={passwordActual}
                onChange={(e) => setPasswordActual(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password-nueva">Contraseña nueva</Label>
              <Input
                id="password-nueva"
                type="password"
                required
                disabled={bloqueada}
                value={passwordNueva}
                onChange={(e) => setPasswordNueva(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password-confirmacion">Confirmar contraseña nueva</Label>
              <Input
                id="password-confirmacion"
                type="password"
                required
                disabled={bloqueada}
                value={confirmacion}
                onChange={(e) => setConfirmacion(e.target.value)}
              />
            </div>

            <Button type="submit" disabled={bloqueada}>
              Cambiar contraseña
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
