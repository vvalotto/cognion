import { Button } from "@/components/ui/button"
import type { VistaProyeccion } from "./vista-proyeccion"

interface Props {
  vista: VistaProyeccion
  enviando: boolean
  onVolver: () => void
  onConfirmar: () => void
}

/**
 * Confirmar finalizar con la pregunta abierta (`#stage-confirmar-finalizar`, §8.5, `US-ADJ-58`): la
 * pregunta no se cierra ni muestra su histograma; las respuestas ya dadas cuentan para el ranking final.
 */
export function StageConfirmarFinalizar({ vista, enviando, onVolver, onConfirmar }: Props) {
  const numero = vista.indice + 1
  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-8 text-center">
      <p className="mb-3.5 text-xl tracking-wider uppercase" style={{ color: "var(--stage-muted)" }}>
        Pregunta {numero} de {vista.cantidadPreguntas} — abierta
      </p>
      <h1 className="text-[40px] leading-tight font-bold">¿Finalizar la sesión ahora?</h1>
      <p className="mt-4 max-w-3xl text-xl" style={{ color: "var(--stage-muted)" }}>
        La pregunta {numero} no se cierra ni muestra su histograma. Las respuestas ya dadas cuentan
        para el ranking final.
      </p>
      <div className="mt-9 flex gap-3.5">
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="h-auto border-white/40 bg-transparent px-9 py-4 text-xl text-white hover:bg-white/10"
          disabled={enviando}
          onClick={onVolver}
        >
          Volver a la pregunta
        </Button>
        <Button
          type="button"
          size="lg"
          className="h-auto px-9 py-4 text-xl"
          disabled={enviando}
          onClick={onConfirmar}
        >
          Finalizar sesión
        </Button>
      </div>
    </div>
  )
}
