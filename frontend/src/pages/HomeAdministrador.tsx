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
    icono: "🏫",
    titulo: "Comisiones",
    descripcion: "Ver, crear y asignar Docentes a Comisiones",
    to: "/comisiones",
  },
  {
    icono: "📘",
    titulo: "Materias",
    descripcion: "Ver y dar de alta Materias",
    to: "/materias",
  },
  {
    icono: "👤",
    titulo: "Alta de Docente",
    descripcion: "Dar de alta un nuevo Docente en el sistema",
    to: "/docentes/nuevo",
  },
  {
    icono: "🔐",
    titulo: "Cuentas",
    descripcion: "Ver, filtrar y resetear cuentas de usuario",
    to: "/cuentas",
  },
]

/**
 * Home del Administrador (`#home-admin`, `wireframes-portal-entrada.md` §2.3, `US-ADJ-30`).
 *
 * Saludo genérico ("Hola, Administrador") — misma decisión que `HomeDocente.tsx`/
 * `HomeEstudiante.tsx` (`US-ADJ-28`/`29`).
 */
export function HomeAdministrador() {
  const navigate = useNavigate()

  return (
    <div>
      <h1 className="text-lg font-semibold">Hola, Administrador</h1>
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
