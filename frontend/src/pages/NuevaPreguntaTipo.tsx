import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

/** Selección de tipo de pregunta (§2.4 `wireframes-banco-preguntas.md`) — paso previo a la carga. */
export function NuevaPreguntaTipo() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Banco de preguntas" },
          { label: "Banco", to: `/materias/${materiaId}/banco` },
          { label: "Nueva pregunta" },
        ]}
      />
      <h1 className="text-lg font-semibold">¿Qué tipo de pregunta querés cargar?</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        El tipo elegido no se puede cambiar después de creada la pregunta.
      </p>

      <div className="mt-4 flex flex-wrap gap-3">
        <Card
          role="button"
          tabIndex={0}
          className="flex-1 cursor-pointer border-2 p-6 text-center transition-colors hover:border-primary"
          onClick={() => navigate(`/materias/${materiaId}/banco/preguntas/nueva/opcion-multiple`)}
          onKeyDown={(e) => {
            if (e.key === "Enter")
              navigate(`/materias/${materiaId}/banco/preguntas/nueva/opcion-multiple`)
          }}
        >
          <p className="font-bold">Opción múltiple</p>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Varias opciones, exactamente una correcta.
          </p>
        </Card>
        <Card
          role="button"
          tabIndex={0}
          className="flex-1 cursor-pointer border-2 p-6 text-center transition-colors hover:border-primary"
          onClick={() => navigate(`/materias/${materiaId}/banco/preguntas/nueva/verdadero-falso`)}
          onKeyDown={(e) => {
            if (e.key === "Enter")
              navigate(`/materias/${materiaId}/banco/preguntas/nueva/verdadero-falso`)
          }}
        >
          <p className="font-bold">Verdadero/Falso</p>
          <p className="mt-1.5 text-sm text-muted-foreground">Una afirmación, respuesta V o F.</p>
        </Card>
      </div>

      <Button
        type="button"
        variant="outline"
        className="mt-4"
        onClick={() => navigate(`/materias/${materiaId}/banco`)}
      >
        Cancelar
      </Button>
    </div>
  )
}
