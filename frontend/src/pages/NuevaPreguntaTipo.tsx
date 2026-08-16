import { useNavigate, useParams } from "react-router"

/** Selección de tipo de pregunta (§2.4 `wireframes-banco-preguntas.md`) — paso previo a la carga. */
export function NuevaPreguntaTipo() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  return (
    <div>
      <p className="text-sm text-muted-foreground">Banco › Nueva pregunta</p>
      <h1 className="text-lg font-semibold">¿Qué tipo de pregunta querés cargar?</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        El tipo elegido no se puede cambiar después de creada la pregunta.
      </p>

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          className="flex-1 rounded-lg border border-border p-4 text-left hover:bg-accent"
          onClick={() =>
            navigate(`/materias/${materiaId}/banco/preguntas/nueva/opcion-multiple`)
          }
        >
          <p className="font-medium">Opción múltiple</p>
          <p className="text-sm text-muted-foreground">
            Varias opciones, exactamente una correcta.
          </p>
        </button>
        <button
          type="button"
          className="flex-1 rounded-lg border border-border p-4 text-left hover:bg-accent"
          onClick={() =>
            navigate(`/materias/${materiaId}/banco/preguntas/nueva/verdadero-falso`)
          }
        >
          <p className="font-medium">Verdadero/Falso</p>
          <p className="text-sm text-muted-foreground">Una afirmación, respuesta V o F.</p>
        </button>
      </div>

      <button
        type="button"
        className="mt-4 rounded-md border border-border px-3 py-1 text-sm hover:bg-accent"
        onClick={() => navigate(`/materias/${materiaId}/banco`)}
      >
        Cancelar
      </button>
    </div>
  )
}
