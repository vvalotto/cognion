import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import { eliminarCuenta, obtenerCuenta, type CuentaDetalleResponse } from "@/lib/cuentas-api"

/**
 * Pantalla de confirmación de eliminación de una cuenta — mismo patrón que
 * `EliminarMateria.tsx`/`EliminarComision.tsx`. Si tiene datos asociados (Comisiones
 * asignadas o creadas, evaluaciones rendidas), el backend la deshabilita en vez de borrarla —
 * de cualquier forma, deja de aparecer en el listado.
 */
export function EliminarCuenta() {
  const { usuarioId } = useParams<{ usuarioId: string }>()
  const navigate = useNavigate()

  const [cuenta, setCuenta] = useState<CuentaDetalleResponse | null>(null)
  const [ultimoAdministrador, setUltimoAdministrador] = useState(false)
  const esAdministrador = cuenta?.perfil === "administrador"

  useEffect(() => {
    if (!usuarioId) return undefined
    const controller = new AbortController()
    obtenerCuenta(usuarioId, controller.signal)
      .then((resultado) => setCuenta(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [usuarioId])

  async function handleEliminar() {
    if (!usuarioId) return
    setUltimoAdministrador(false)
    try {
      await eliminarCuenta(usuarioId)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setUltimoAdministrador(true)
        return
      }
      throw err
    }
    void navigate("/cuentas")
  }

  function handleCancelar() {
    void navigate("/cuentas")
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Administración" },
          { label: "Cuentas", to: "/cuentas" },
          { label: esAdministrador ? "Deshabilitar" : "Eliminar" },
        ]}
      />
      <h1 className="text-lg font-semibold">
        {esAdministrador ? "Deshabilitar cuenta" : "Eliminar cuenta"}
      </h1>
      {esAdministrador && (
        <p className="text-sm text-muted-foreground">Cuenta de Administrador</p>
      )}

      {ultimoAdministrador && (
        <div
          role="alert"
          className="mt-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <span aria-hidden="true">⛔</span>
          <div>
            <p className="font-medium">No se puede deshabilitar esta cuenta</p>
            <p>
              Es el único Administrador operativo. El sistema necesita al menos uno activo:
              habilitá primero a otro Administrador y volvé a intentar.
            </p>
          </div>
        </div>
      )}

      <Card className="mt-4 p-4">
        <p className="text-sm text-muted-foreground">
          {esAdministrador ? "Cuenta a deshabilitar:" : "Cuenta a eliminar:"}
        </p>
        <p className="mt-1 font-medium">{cuenta?.nombre ?? "…"}</p>
        {cuenta && <p className="text-sm text-muted-foreground">{cuenta.email}</p>}
      </Card>

      <div
        role="alert"
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        {esAdministrador ? (
          <p>
            <strong>Un Administrador nunca se borra.</strong> La cuenta se deshabilita: deja de
            poder iniciar sesión, pero no se pierde nada y se puede reactivar desde el listado.
            No se puede deshabilitar al único Administrador operativo.
          </p>
        ) : (
        <p>
          Si tiene datos asociados (Comisiones asignadas o creadas, evaluaciones rendidas), la
          cuenta se deshabilita en vez de borrarse — deja de poder iniciar sesión, pero no afecta
          lo que ya existe. <strong>Si no tiene datos asociados, se borra en forma permanente y
          no se puede deshacer.</strong>
        </p>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <Button variant="destructive-solid" onClick={handleEliminar}>
          {esAdministrador ? "Sí, deshabilitar" : "Sí, eliminar"}
        </Button>
        <Button variant="outline" onClick={handleCancelar}>
          Cancelar
        </Button>
      </div>
    </div>
  )
}
