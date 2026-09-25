import type { MensajeSesionEnVivo, RankingItemCanal } from "@/lib/canal-sesion-en-vivo"
import type { EstadoSesionEnVivoResponse } from "@/lib/sesion-en-vivo-api"

export type EtapaEstudiante =
  | "sala"
  | "espera-opciones"
  | "pregunta"
  | "resultado"
  | "sin-respuesta"
  | "finalizada"

/** `cierre`: el Docente cerró sin que respondiera (H4); `tiempo`: su toque llegó tarde (H5). */
export type MotivoSinRespuesta = "cierre" | "tiempo"

/** Resultado de la última respuesta; `null` si no se conoce (por ejemplo, tras recargar). */
export interface ResultadoRespuesta {
  esCorrecta: boolean
  puntaje: number
}

export interface VistaEstudiante {
  etapa: EtapaEstudiante
  totalParticipantes: number
  /** Índice 0-based de la pregunta actual (la pantalla muestra `indice + 1`). */
  indice: number
  cantidadPreguntas: number
  preguntaId: string
  enunciado: string
  tipo: string
  opciones: string[] | null
  tiempoLimiteSegundos: number
  inicioOpcionesMs: number
  puntajeAcumulado: number
  resultado: ResultadoRespuesta | null
  motivoSinRespuesta: MotivoSinRespuesta
  ranking: RankingItemCanal[] | null
}

function etapaEnCurso(estado: EstadoSesionEnVivoResponse, trasRechazo: boolean): EtapaEstudiante {
  if (estado.yaRespondio) return "resultado"
  if (estado.preguntaActualCerrada) return "sin-respuesta"
  if (!estado.opcionesMostradas) return "espera-opciones"
  // Con la pregunta abierta y sin respuesta, un rechazo del servidor solo puede ser tiempo agotado.
  return trasRechazo ? "sin-respuesta" : "pregunta"
}

/**
 * Etapa que le corresponde al estado del servidor. `trasRechazo`: se recalcula después de un `422` al
 * responder — el `detail` es texto libre, así que el motivo se deduce del estado y no del mensaje.
 */
export function calcularVistaEstudiante(
  estado: EstadoSesionEnVivoResponse,
  { trasRechazo = false }: { trasRechazo?: boolean } = {},
): VistaEstudiante {
  const etapa: EtapaEstudiante =
    estado.estado === "en_espera"
      ? "sala"
      : estado.estado === "finalizada"
        ? "finalizada"
        : etapaEnCurso(estado, trasRechazo)
  const pregunta = estado.preguntaActual
  return {
    etapa,
    totalParticipantes: estado.totalParticipantes,
    indice: estado.preguntaActualIndice ?? 0,
    cantidadPreguntas: estado.cantidadPreguntas,
    preguntaId: pregunta?.preguntaId ?? "",
    enunciado: pregunta?.enunciado ?? "",
    tipo: pregunta?.tipo ?? "",
    opciones: pregunta?.opciones ?? null,
    tiempoLimiteSegundos: estado.tiempoLimitePorPreguntaSegundos,
    inicioOpcionesMs: estado.opcionesMostradasEn ? Date.parse(estado.opcionesMostradasEn) : Date.now(),
    puntajeAcumulado: estado.puntajeAcumulado ?? 0,
    resultado: null,
    motivoSinRespuesta: estado.preguntaActualCerrada ? "cierre" : "tiempo",
    ranking: null,
  }
}

/**
 * Aplica un mensaje del canal. Devuelve `"recalcular"` si el mensaje no encaja con la pregunta que se
 * está mostrando (se perdió alguno). El celular nunca muestra la correcta ni el ranking antes del final.
 */
export function aplicarMensajeEstudiante(
  vista: VistaEstudiante,
  mensaje: MensajeSesionEnVivo,
  ahoraMs: number = Date.now(),
): VistaEstudiante | "recalcular" {
  switch (mensaje.tipo) {
    case "participantes_actualizados":
      return { ...vista, totalParticipantes: mensaje.cantidad }
    case "pregunta_presentada":
      if (vista.etapa === "finalizada") return vista
      return {
        ...vista,
        etapa: "espera-opciones",
        indice: mensaje.preguntaActualIndice,
        preguntaId: mensaje.pregunta.preguntaId,
        enunciado: mensaje.pregunta.enunciado,
        tipo: mensaje.pregunta.tipo,
        opciones: null,
        resultado: null,
      }
    case "opciones_mostradas":
      if (mensaje.preguntaActualIndice !== vista.indice) return "recalcular"
      if (vista.etapa !== "espera-opciones") return vista
      return {
        ...vista,
        etapa: "pregunta",
        opciones: mensaje.opciones,
        tiempoLimiteSegundos: mensaje.tiempoLimitePorPreguntaSegundos,
        inicioOpcionesMs: ahoraMs,
      }
    case "pregunta_cerrada":
      if (mensaje.preguntaActualIndice !== vista.indice) return "recalcular"
      if (vista.etapa !== "pregunta" && vista.etapa !== "espera-opciones") return vista
      return { ...vista, etapa: "sin-respuesta", motivoSinRespuesta: "cierre" }
    case "sesion_finalizada":
      return { ...vista, etapa: "finalizada", ranking: mensaje.ranking }
    default:
      return vista
  }
}

/** Resultado de una respuesta aceptada por el servidor. */
export function registrarRespuesta(
  vista: VistaEstudiante,
  respuesta: { esCorrecta: boolean; puntaje: number; puntajeAcumulado: number },
): VistaEstudiante {
  return {
    ...vista,
    etapa: "resultado",
    resultado: { esCorrecta: respuesta.esCorrecta, puntaje: respuesta.puntaje },
    puntajeAcumulado: respuesta.puntajeAcumulado,
  }
}

const TIPO_VERDADERO_FALSO = "verdadero_falso"

/** Contenido que se manda al responder la opción en la posición `indice`: `{valor}` o `{opcion_indice}`. */
export function contenidoRespuesta(tipo: string, indice: number): Record<string, unknown> {
  return tipo === TIPO_VERDADERO_FALSO ? { valor: indice === 0 } : { opcion_indice: indice }
}
