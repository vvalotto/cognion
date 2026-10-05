import { useLocation } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"

interface FueraDePeriodoState {
  titulo?: string
  estado?: "todavia_no_abrio" | "cerrada"
  fechaApertura?: string
  fechaCierre?: string
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

/** Pantalla "Fuera de período" del Estudiante (`#est-fuera-periodo*`, `US-3.4.5`, `US-ADJ-61`).
 *
 * Tres variantes según el contexto con el que se llega: "todavía no abrió" (`estado` o, sin él,
 * una `fechaApertura`), "ya cerró" (`estado = "cerrada"`) y un texto neutro cuando no llega
 * contexto (el `422 FueraDePeriodo` de `IniciarEvaluacion` o un link directo no dicen el motivo).
 * Recibe título y fechas por navigation state desde `MisActividades` — no hay un endpoint de
 * detalle de actividad accesible al rol `estudiante` (`GET /actividades/{id}` es solo `docente`).
 */
export function FueraDePeriodo() {
  const { state } = useLocation()
  const { titulo, estado, fechaApertura, fechaCierre } =
    (state as FueraDePeriodoState | null) ?? {}
  const variante = estado ?? (fechaApertura ? "todavia_no_abrio" : undefined)

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
        {variante === "cerrada" ? (
          <>
            <p className="mb-2 text-3xl text-muted-foreground">🔒</p>
            <h2 className="mb-2 font-semibold">Esta actividad ya cerró</h2>
            <p className="text-sm text-muted-foreground">
              {fechaCierre && (
                <>
                  Cerró el <strong>{formatearFecha(fechaCierre)}</strong>.{" "}
                </>
              )}
              Ya no se puede rendir.
            </p>
          </>
        ) : variante === "todavia_no_abrio" ? (
          <>
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
          </>
        ) : (
          <>
            <p className="mb-2 text-3xl text-muted-foreground">ℹ️</p>
            <h2 className="mb-2 font-semibold">
              Esta actividad no está disponible en este momento
            </h2>
          </>
        )}
      </Card>
    </div>
  )
}
