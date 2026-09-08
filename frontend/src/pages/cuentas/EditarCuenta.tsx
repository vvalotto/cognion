import { useEffect, useRef, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError } from "@/lib/api-client"
import { editarCuenta, obtenerCuenta, type CuentaDetalleResponse } from "@/lib/cuentas-api"

/**
 * Pantalla de edición de nombre/email de una cuenta — corrige datos cargados con error al
 * dar de alta. No toca password, bloqueo ni rol (para eso está "Resetear contraseña").
 */
export function EditarCuenta() {
  const { usuarioId } = useParams<{ usuarioId: string }>()
  const navigate = useNavigate()

  const [cuenta, setCuenta] = useState<CuentaDetalleResponse | null>(null)
  const [nombre, setNombre] = useState("")
  const [email, setEmail] = useState("")
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!usuarioId) return undefined
    const controller = new AbortController()
    obtenerCuenta(usuarioId, controller.signal)
      .then((resultado) => {
        setCuenta(resultado)
        setNombre(resultado.nombre)
        setEmail(resultado.email)
      })
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

    try {
      await editarCuenta(usuarioId, nombre, email, controladorSubmitRef.current?.signal)
      void navigate(`/cuentas/${usuarioId}`)
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 409) {
        setError("Ya existe otra cuenta con ese email.")
        return
      }
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
          { label: "Editar" },
        ]}
      />
      <h1 className="text-lg font-semibold">Editar cuenta</h1>
      <p className="text-sm text-muted-foreground">
        Corregí el nombre o el email si se cargaron con un error — no cambia la contraseña ni
        el rol.
      </p>

      <Card className="mt-4">
        <CardContent>
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
              <Label htmlFor="editar-cuenta-nombre">Nombre completo</Label>
              <Input
                id="editar-cuenta-nombre"
                type="text"
                required
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="editar-cuenta-email">Email</Label>
              <Input
                id="editar-cuenta-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="flex gap-2">
              <Button type="submit">Guardar cambios</Button>
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
