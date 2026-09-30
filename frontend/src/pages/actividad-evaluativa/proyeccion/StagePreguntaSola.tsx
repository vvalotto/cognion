import { Button } from "@/components/ui/button"
import type { VistaProyeccion } from "./vista-proyeccion"

interface Props {
  vista: VistaProyeccion
  enviando: boolean
  onMostrarOpciones: () => void
  /** Abre la confirmación de finalizar con la pregunta abierta (§8.4, `US-ADJ-58`). */
  onFinalizar: () => void
}

/** Proyección — pregunta sola, sin opciones (`#stage-pregunta-sola`, §2.3). */
export function StagePreguntaSola({ vista, enviando, onMostrarOpciones, onFinalizar }: Props) {
  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-8 text-center">
      <p className="mb-3.5 text-xl tracking-wider uppercase" style={{ color: "var(--stage-muted)" }}>
        Pregunta {vista.indice + 1} de {vista.cantidadPreguntas}
      </p>
      <h1 className="text-[40px] leading-tight font-bold">{vista.enunciado}</h1>
      <div className="mt-9 flex gap-3.5">
        <Button
          type="button"
          size="lg"
          className="h-auto px-9 py-4 text-xl"
          disabled={enviando}
          onClick={onMostrarOpciones}
        >
          Mostrar opciones
        </Button>
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
