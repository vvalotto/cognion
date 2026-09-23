import type {
  MensajeSesionEnVivo,
  OpcionDistribuidaCanal,
  RankingItemCanal,
  RespuestaCorrectaCanal,
} from "@/lib/canal-sesion-en-vivo"
import type { EstadoSesionEnVivoResponse } from "@/lib/sesion-en-vivo-api"

export type EtapaProyeccion = "pregunta-sola" | "pregunta-opciones" | "cerrada" | "finalizada"

/** Resultado de la pregunta cerrada o de la sesión — lo consume `US-6.3.7`. */
export interface ResultadoProyeccion {
  respuestaCorrecta: RespuestaCorrectaCanal | null
  distribucion: OpcionDistribuidaCanal[]
  ranking: RankingItemCanal[]
}

export interface VistaProyeccion {
  etapa: EtapaProyeccion
  /** Índice 0-based de la pregunta actual (el eyebrow muestra `indice + 1`). */
  indice: number
  cantidadPreguntas: number
  enunciado: string
  tipo: string
  opciones: string[] | null
  tiempoLimiteSegundos: number
  inicioOpcionesMs: number
  cantidadRespuestas: number
  totalParticipantes: number
  resultado: ResultadoProyeccion | null
}

/** Etapa que le corresponde al estado del servidor; `null` si la sesión no arrancó (→ sala). */
export function calcularVista(estado: EstadoSesionEnVivoResponse): VistaProyeccion | null {
  if (estado.estado === "en_espera") return null

  const pregunta = estado.preguntaActual
  const resultadoServidor = estado.resultadoPregunta
  const resultado: ResultadoProyeccion | null = resultadoServidor
    ? {
        respuestaCorrecta: pregunta?.respuestaCorrecta ?? null,
        distribucion: resultadoServidor.distribucion,
        ranking: resultadoServidor.ranking,
      }
    : null

  let etapa: EtapaProyeccion
  if (estado.estado === "finalizada") etapa = "finalizada"
  else if (estado.preguntaActualCerrada) etapa = "cerrada"
  else if (estado.opcionesMostradas) etapa = "pregunta-opciones"
  else etapa = "pregunta-sola"

  return {
    etapa,
    indice: estado.preguntaActualIndice ?? 0,
    cantidadPreguntas: estado.cantidadPreguntas,
    enunciado: pregunta?.enunciado ?? "",
    tipo: pregunta?.tipo ?? "",
    opciones: pregunta?.opciones ?? null,
    tiempoLimiteSegundos: estado.tiempoLimitePorPreguntaSegundos,
    inicioOpcionesMs: estado.opcionesMostradasEn
      ? Date.parse(estado.opcionesMostradasEn)
      : Date.now(),
    cantidadRespuestas: estado.cantidadRespuestas,
    totalParticipantes: estado.totalParticipantes,
    resultado,
  }
}

/**
 * Aplica un mensaje del canal a la vista. Devuelve `"recalcular"` si el mensaje no encaja con la
 * pregunta que se está mostrando (se perdió alguno) — el llamador vuelve a pedir el estado.
 */
export function aplicarMensaje(
  vista: VistaProyeccion,
  mensaje: MensajeSesionEnVivo,
  ahoraMs: number,
): VistaProyeccion | "recalcular" {
  switch (mensaje.tipo) {
    case "participantes_actualizados":
      return { ...vista, totalParticipantes: mensaje.cantidad }
    case "pregunta_presentada":
      return {
        ...vista,
        etapa: "pregunta-sola",
        indice: mensaje.preguntaActualIndice,
        enunciado: mensaje.pregunta.enunciado,
        tipo: mensaje.pregunta.tipo,
        opciones: null,
        cantidadRespuestas: 0,
        resultado: null,
      }
    case "opciones_mostradas":
      if (mensaje.preguntaActualIndice !== vista.indice) return "recalcular"
      return {
        ...vista,
        etapa: "pregunta-opciones",
        opciones: mensaje.opciones,
        tiempoLimiteSegundos: mensaje.tiempoLimitePorPreguntaSegundos,
        inicioOpcionesMs: ahoraMs,
        cantidadRespuestas: mensaje.cantidadRespuestas,
      }
    case "conteo_respuestas_actualizado":
      if (mensaje.preguntaActualIndice !== vista.indice) return vista
      return { ...vista, cantidadRespuestas: mensaje.cantidadRespuestas }
    case "pregunta_cerrada":
      if (mensaje.preguntaActualIndice !== vista.indice) return "recalcular"
      return {
        ...vista,
        etapa: "cerrada",
        resultado: {
          respuestaCorrecta: mensaje.respuestaCorrecta,
          distribucion: mensaje.distribucion,
          ranking: mensaje.ranking,
        },
      }
    case "sesion_finalizada":
      return {
        ...vista,
        etapa: "finalizada",
        resultado: { respuestaCorrecta: null, distribucion: [], ranking: mensaje.ranking },
      }
  }
}
