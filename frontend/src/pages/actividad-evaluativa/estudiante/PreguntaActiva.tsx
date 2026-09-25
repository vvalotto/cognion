import { estiloOpcion, opcionesEnVivo } from "@/lib/opciones-en-vivo"
import { formatearTemporizador, useSegundosRestantes } from "@/lib/temporizador-pregunta"
import { BarraPregunta } from "./BarraPregunta"
import { contenidoRespuesta, type VistaEstudiante } from "./vista-estudiante"

interface Props {
  vista: VistaEstudiante
  enviando: boolean
  onResponder: (contenido: Record<string, unknown>) => void
}

/**
 * Pregunta activa (`#est-pregunta`, §3.3): tarjetas táctiles del mismo color que la proyección.
 * Tocar responde al instante — un solo intento (INV-AEV-07), sin botón de confirmación.
 */
export function PreguntaActiva({ vista, enviando, onResponder }: Props) {
  const restantes = useSegundosRestantes(vista.tiempoLimiteSegundos, vista.inicioOpcionesMs)
  const opciones = opcionesEnVivo(vista.tipo, vista.opciones)

  return (
    <div className="mx-auto max-w-md">
      <BarraPregunta
        indice={vista.indice}
        cantidadPreguntas={vista.cantidadPreguntas}
        extra={
          <strong role="timer" aria-label="Tiempo restante" className="text-destructive tabular-nums">
            {formatearTemporizador(restantes)}
          </strong>
        }
      />
      <h1 className="mt-2 mb-3.5 text-[17px] font-semibold">{vista.enunciado}</h1>
      <div className="grid grid-cols-2 gap-3">
        {opciones.map((opcion, posicion) => (
          <button
            key={`${posicion}-${opcion.texto}`}
            type="button"
            data-color={opcion.color}
            disabled={enviando}
            onClick={() => onResponder(contenidoRespuesta(vista.tipo, posicion))}
            className={`flex min-h-[110px] items-center rounded-2xl p-4 text-left text-base leading-tight font-bold transition-transform active:scale-95 disabled:opacity-60${
              opciones.length === 3 && posicion === 2 ? " col-span-2" : ""
            }`}
            style={estiloOpcion(opcion.color)}
          >
            {opcion.texto}
          </button>
        ))}
      </div>
      <p className="mt-3.5 text-center text-xs text-muted-foreground">
        Tocá una tarjeta para responder — un solo intento, no se puede cambiar después.
      </p>
    </div>
  )
}
