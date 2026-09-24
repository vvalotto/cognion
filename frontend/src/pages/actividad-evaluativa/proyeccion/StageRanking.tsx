import { Button } from "@/components/ui/button"
import { ListaRanking } from "./ListaRanking"
import type { VistaProyeccion } from "./vista-proyeccion"

interface Props {
  vista: VistaProyeccion
  enviando: boolean
  onSiguiente: () => void
  onFinalizar: () => void
}

/** Proyección — ranking Top 3 tras la pregunta (`#stage-ranking`, §2.6). */
export function StageRanking({ vista, enviando, onSiguiente, onFinalizar }: Props) {
  const quedanPreguntas = vista.indice + 1 < vista.cantidadPreguntas

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-8 text-center">
      <p className="text-xl tracking-wider uppercase" style={{ color: "var(--stage-muted)" }}>
        Ranking — tras la pregunta {vista.indice + 1} de {vista.cantidadPreguntas}
      </p>
      <ListaRanking ranking={vista.resultado?.ranking ?? []} />
      <div className="mt-9 flex gap-4">
        {quedanPreguntas && (
          <Button
            type="button"
            size="lg"
            className="h-auto px-9 py-4 text-xl"
            disabled={enviando}
            onClick={onSiguiente}
          >
            Siguiente pregunta
          </Button>
        )}
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="h-auto border-white/40 bg-transparent px-9 py-4 text-xl text-white hover:bg-white/10"
          disabled={enviando}
          onClick={onFinalizar}
        >
          Finalizar sesión
        </Button>
      </div>
    </div>
  )
}
