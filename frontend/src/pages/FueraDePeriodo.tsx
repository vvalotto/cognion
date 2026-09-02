import { useLocation } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"

interface FueraDePeriodoState {
  titulo?: string
  fechaApertura?: string
}

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

/** Pantalla "Fuera de período" del Estudiante (`#est-fuera-periodo`, `US-3.4.5`).
 *
 * Un único mensaje cubre "antes de apertura" y "después de cierre, nunca iniciada" (mismo
 * criterio del prototipo aprobado — sin distinguir el motivo al Estudiante). Recibe título y
 * `fecha_apertura` por navigation state desde `MisActividades` — no hay un endpoint de detalle
 * de actividad accesible al rol `estudiante` (`GET /actividades/{id}` es solo `docente`).
 */
export function FueraDePeriodo() {
  const { state } = useLocation()
  const { titulo, fechaApertura } = (state as FueraDePeriodoState | null) ?? {}

  return (
    <div className="mx-auto max-w-md">
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/mis-actividades/materias" },
          { label: "Actividades" },
          { label: titulo ?? "…" },
        ]}
      />
      <h1 className="text-lg font-semibold">{titulo ?? "Actividad"}</h1>

      <Card className="mt-4 p-6 text-center">
        <p className="mb-2 text-3xl text-muted-foreground">🕒</p>
        <h2 className="mb-2 font-semibold">Todavía no está disponible</h2>
        <p className="text-sm text-muted-foreground">
          {fechaApertura ? (
            <>
              Esta actividad abre el <strong>{formatearFecha(fechaApertura)}</strong>. Volvé a
              entrar a partir de ese momento.
            </>
          ) : (
            "Volvé a entrar cuando la actividad esté disponible."
          )}
        </p>
      </Card>

      <p className="mt-4 text-center text-xs text-muted-foreground">
        El mismo mensaje aparece si volvés a entrar después del cierre y nunca iniciaste la
        evaluación — en ese caso indica que el período ya terminó.
      </p>
    </div>
  )
}
