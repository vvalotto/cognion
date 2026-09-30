import { Button } from "@/components/ui/button"
import { estiloOpcion, opcionesEnVivo } from "@/lib/opciones-en-vivo"
import { formatearTemporizador, useSegundosRestantes } from "@/lib/temporizador-pregunta"
import type { VistaProyeccion } from "./vista-proyeccion"

interface Props {
  vista: VistaProyeccion
  enviando: boolean
  onCerrarPregunta: () => void
  /** Abre la confirmación de finalizar con la pregunta abierta (§8.4, `US-ADJ-58`). */
  onFinalizar: () => void
}

/** Proyección — pregunta con opciones, temporizador y conteo (`#stage-pregunta-opciones`, §2.4). */
export function StagePreguntaOpciones({ vista, enviando, onCerrarPregunta, onFinalizar }: Props) {
  const restantes = useSegundosRestantes(vista.tiempoLimiteSegundos, vista.inicioOpcionesMs)
  const opciones = opcionesEnVivo(vista.tipo, vista.opciones)
  const progreso =
    vista.tiempoLimiteSegundos > 0 ? (restantes / vista.tiempoLimiteSegundos) * 100 : 0

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-8 text-center">
      <p className="mb-3.5 text-xl tracking-wider uppercase" style={{ color: "var(--stage-muted)" }}>
        Pregunta {vista.indice + 1} de {vista.cantidadPreguntas}
      </p>
      <h1 className="mb-5 text-[30px] leading-tight font-bold">{vista.enunciado}</h1>

      <p role="timer" aria-label="Tiempo restante" className="text-6xl font-black tabular-nums">
        {formatearTemporizador(restantes)}
      </p>
      <div
        className="mt-2 mb-7 h-3.5 w-full max-w-[700px] overflow-hidden rounded-full"
        style={{ background: "rgba(255,255,255,0.12)" }}
      >
        <div
          data-testid="barra-progreso"
          className="h-full"
          style={{ width: `${progreso}%`, background: "var(--stage-accent)" }}
        />
      </div>

      <ul className="grid w-full max-w-4xl grid-cols-2 gap-4">
        {opciones.map((opcion, posicion) => (
          <li
            key={`${posicion}-${opcion.texto}`}
            data-color={opcion.color}
            className={`rounded-xl px-6 py-6 text-[28px] leading-snug font-bold${
              opciones.length === 3 && posicion === 2 ? " col-span-2" : ""
            }`}
            style={estiloOpcion(opcion.color)}
          >
            {opcion.texto}
          </li>
        ))}
      </ul>

      <p className="mt-7 text-[28px] font-bold">
        <span className="text-[34px]" style={{ color: "var(--stage-primary)" }}>
          {vista.cantidadRespuestas}
        </span>{" "}
        / {vista.totalParticipantes} ya respondieron
      </p>

      <div className="mt-8 flex gap-3.5">
        <Button
          type="button"
          variant="destructive-solid"
          size="lg"
          className="h-auto px-9 py-4 text-xl"
          disabled={enviando}
          onClick={onCerrarPregunta}
        >
          Cerrar pregunta
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
