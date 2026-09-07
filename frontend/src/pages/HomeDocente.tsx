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
    icono: "📚",
    titulo: "Banco de Preguntas",
    descripcion: "Cargar, editar y filtrar preguntas por materia",
    to: "/materias",
  },
  {
    icono: "📝",
    titulo: "Actividades",
    descripcion: "Crear y administrar actividades de evaluación",
    to: "/actividad-evaluativa/materias",
  },
  {
    icono: "📊",
    titulo: "Desempeño por alumno",
    descripcion: "Consultar el desempeño acumulado de un estudiante",
    to: "/analytics/desempeno-por-alumno",
  },
  {
    icono: "📈",
    titulo: "Desempeño por tema",
    descripcion: "Ver la tasa de error por unidad/tema",
    to: "/analytics/desempeno-por-tema",
  },
]

/**
 * Home del Docente (`#home-docente`, `wireframes-portal-entrada.md` §2.1, `US-ADJ-28`).
 *
 * Saludo genérico ("Hola, Docente") en vez de "Hola, {nombre}" del wireframe — decisión de
 * Fase 0: ningún endpoint expone el nombre del propio usuario autenticado sin agregar
 * backend nuevo (ver `docs/specs/ajustes/US-ADJ-28.md` §Contexto del dominio).
 */
export function HomeDocente() {
  const navigate = useNavigate()

  return (
    <div>
      <h1 className="text-lg font-semibold">Hola, Docente</h1>
      <p className="mt-1 text-sm text-muted-foreground">Accesos directos a las áreas del Docente.</p>

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
