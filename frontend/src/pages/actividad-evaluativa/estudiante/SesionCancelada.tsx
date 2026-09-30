import { Link } from "react-router"

import { Card } from "@/components/ui/card"

/** Sesión cancelada por el Docente antes de iniciarla (`#est-sesion-cancelada`, §8.3, `US-ADJ-58`). */
export function SesionCancelada() {
  return (
    <Card className="mx-auto mt-10 max-w-md p-6 text-center">
      <div className="text-4xl" aria-hidden="true">
        🚫
      </div>
      <h1 className="mt-2 text-lg font-semibold">El Docente canceló la sesión</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Esta sesión en vivo no se va a dar. No se registró ninguna respuesta.
      </p>
      <Link
        to="/mis-actividades/materias"
        className="mt-4 inline-flex w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
      >
        Volver a mis actividades
      </Link>
    </Card>
  )
}
