import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"

interface CardInforme {
  icono: string
  titulo: string
  descripcion: string
  to: string
}

const CARDS: CardInforme[] = [
  {
    icono: "📊",
    titulo: "Desempeño por comisión",
    descripcion: "Tabla de estudiantes con % de aciertos y drill-down a la revisión de una evaluación",
    to: "/analytics/desempeno-por-comision",
  },
  {
    icono: "🧑‍🎓",
    titulo: "Desempeño por alumno",
    descripcion: "Consultar el desempeño acumulado de un estudiante elegido",
    to: "/analytics/desempeno-por-alumno",
  },
  {
    icono: "📈",
    titulo: "Desempeño por tema",
    descripcion: "Tasa de error agregada por unidad temática y tema",
    to: "/analytics/desempeno-por-tema",
  },
  {
    icono: "❗",
    titulo: "Preguntas más falladas",
    descripcion: "Ranking de preguntas ordenado por tasa de error",
    to: "/analytics/ranking-preguntas-falladas",
  },
]

/** Landing de Analytics — reúne los 4 informes del Docente en un solo punto de entrada del menú. */
export function Analytics() {
  const navigate = useNavigate()

  return (
    <div>
      <Breadcrumb items={[{ label: "Reportes" }]} />
      <h1 className="text-lg font-semibold">Reportes</h1>
      <p className="mt-1 text-sm text-muted-foreground">Elegí un informe para ver el desempeño de tus estudiantes.</p>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {CARDS.map((card) => (
          <Card
            key={card.to}
            role="button"
            tabIndex={0}
            className="cursor-pointer p-5 transition-colors hover:border-primary"
            onClick={() => navigate(card.to)}
            onKeyDown={(e) => {
              if (e.key === "Enter") navigate(card.to)
            }}
          >
            <p className="mb-2 text-xl">{card.icono}</p>
            <p className="font-semibold">{card.titulo}</p>
            <p className="mt-1 text-xs text-muted-foreground">{card.descripcion}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
