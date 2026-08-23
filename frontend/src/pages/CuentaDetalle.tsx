import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { obtenerCuenta, type CuentaDetalleResponse } from "@/lib/cuentas-api"
import type { Rol } from "@/lib/session"

const ETIQUETA_ROL: Record<Rol, string> = {
  administrador: "Administrador",
  docente: "Docente",
  estudiante: "Estudiante",
}

const VARIANTE_ROL: Record<Rol, "rol-docente" | "rol-estudiante" | "rol-admin"> = {
  docente: "rol-docente",
  estudiante: "rol-estudiante",
  administrador: "rol-admin",
}

/** Pantalla de detalle de cuenta (§2.2 `wireframes-cuentas-administracion.md`). */
export function CuentaDetalle() {
  const { usuarioId } = useParams<{ usuarioId: string }>()
  const navigate = useNavigate()

  const [cuenta, setCuenta] = useState<CuentaDetalleResponse | null>(null)

  useEffect(() => {
    if (!usuarioId) return
    let cancelado = false
    obtenerCuenta(usuarioId).then((resultado) => {
      if (!cancelado) setCuenta(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [usuarioId])

  if (!cuenta) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Administración" },
          { label: "Cuentas", to: "/cuentas" },
          { label: cuenta.nombre },
        ]}
      />
      <h1 className="text-lg font-semibold">{cuenta.nombre}</h1>
      <p className="text-sm text-muted-foreground">Detalle de cuenta</p>

      {cuenta.bloqueada && (
        <div
          role="alert"
          className="mt-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <span aria-hidden="true">🔒</span>
          <div>
            <p className="font-medium">Cuenta bloqueada</p>
            <p className="mt-1">
              3 intentos fallidos consecutivos de inicio de sesión. No puede volver a intentar
              hasta que se resetee su contraseña.
            </p>
          </div>
        </div>
      )}

      <Card className="mt-4 p-4 text-sm">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
          <dt className="text-muted-foreground">Email</dt>
          <dd>{cuenta.email}</dd>
          <dt className="text-muted-foreground">Rol</dt>
          <dd>
            <Badge variant={VARIANTE_ROL[cuenta.perfil]}>{ETIQUETA_ROL[cuenta.perfil]}</Badge>
          </dd>
          <dt className="text-muted-foreground">Estado</dt>
          <dd>
            <Badge variant={cuenta.bloqueada ? "estado-bloqueada" : "estado-activa"}>
              {cuenta.bloqueada ? "Bloqueada" : "Activa"}
            </Badge>
          </dd>
          {cuenta.perfil === "estudiante" && cuenta.comisionId && (
            <>
              <dt className="text-muted-foreground">Comisión</dt>
              <dd>{cuenta.comisionId}</dd>
            </>
          )}
          <dt className="text-muted-foreground">Fecha de creación</dt>
          <dd>{new Date(cuenta.creadoEn).toLocaleDateString()}</dd>
        </dl>
      </Card>

      <Button
        variant="destructive-solid"
        className="mt-4 w-full"
        onClick={() => navigate(`/cuentas/${cuenta.id}/resetear-password`)}
      >
        Resetear contraseña y desbloquear
      </Button>
      <p className="mt-2 text-center text-sm text-muted-foreground">
        Es la única forma de desbloquear la cuenta — no existe una acción de "desbloquear"
        separada.
      </p>
    </div>
  )
}
