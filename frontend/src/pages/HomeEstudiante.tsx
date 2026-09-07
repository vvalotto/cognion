import { useNavigate } from "react-router"

import { Card } from "@/components/ui/card"

interface CardAcceso {
  icono: string
  titulo: string
  descripcion: string
  to: string
}

const CARDS: CardAcceso[] = [
  {
    icono: "📝",
    titulo: "Mis Actividades",
    descripcion: "Ver y rendir las actividades disponibles",
    to: "/mis-actividades/materias",
  },
  {
    icono: "📊",
    titulo: "Mi Desempeño",
    descripcion: "Ver el resultado acumulado de mis evaluaciones",
    to: "/analytics/mi-desempeno",
  },
]

/**
 * Home del Estudiante (`#home-estudiante`, `wireframes-portal-entrada.md` §2.2, `US-ADJ-29`).
 *
 * Saludo genérico ("Hola, Estudiante") — misma decisión que `HomeDocente.tsx` (`US-ADJ-28`):
 * ningún endpoint expone el nombre del propio usuario autenticado.
 */
export function HomeEstudiante() {
  const navigate = useNavigate()

  return (
    <div>
      <h1 className="text-lg font-semibold">Hola, Estudiante</h1>
      <p className="mt-1 text-sm text-muted-foreground">Accesos directos a tus áreas.</p>

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
