import { router } from "@/router"
import { clearSession, getSession } from "@/lib/session"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
const BACKOFF_INICIAL_MS = 1000
const BACKOFF_TOPE_MS = 10000
const CODIGO_CIERRE_TOKEN_INVALIDO = 1008

export interface ParticipanteEnVivo {
  estudianteId: string
  nombre: string
  unidoEn: string
}

export interface PreguntaPresentada {
  preguntaId: string
  enunciado: string
  tipo: string
}

export interface RespuestaCorrectaCanal {
  contenido: Record<string, unknown>
  texto: string
  opciones: string[] | null
}

export interface OpcionDistribuidaCanal {
  opcion: string
  cantidad: number
}

export interface RankingItemCanal {
  posicion: number
  estudianteId: string
  nombre: string
  puntajeAcumulado: number
}

export type MensajeSesionEnVivo =
  | {
      tipo: "participantes_actualizados"
      cantidad: number
      participantes: ParticipanteEnVivo[]
    }
  | {
      tipo: "pregunta_presentada"
      preguntaActualIndice: number
      pregunta: PreguntaPresentada
    }
  | {
      tipo: "opciones_mostradas"
      preguntaActualIndice: number
      opciones: string[] | null
      tiempoLimitePorPreguntaSegundos: number
      cantidadRespuestas: number
    }
  | {
      tipo: "conteo_respuestas_actualizado"
      preguntaActualIndice: number
      cantidadRespuestas: number
    }
  | {
      tipo: "pregunta_cerrada"
      preguntaActualIndice: number
      respuestaCorrecta: RespuestaCorrectaCanal
      distribucion: OpcionDistribuidaCanal[]
      ranking: RankingItemCanal[]
    }
  | {
      tipo: "sesion_finalizada"
      ranking: RankingItemCanal[]
    }

export type EstadoCanal = "conectado" | "reconectando" | "desconectado"

export type WebSocketFactory = (url: string) => WebSocket

function urlBase(): string {
  return BASE_URL.replace(/^http/, "ws")
}

/**
 * Envuelve el `WebSocket` nativo hacia `/sesiones-en-vivo/{id}/canal`: solo recibe mensajes del
 * servidor (los comandos van por HTTP, `ADR-005`), se reconecta con backoff exponencial y avisa
 * la re-sincronización — nunca asume que no se perdió un mensaje durante el corte.
 */
export class CanalSesionEnVivo {
  private readonly sesionId: string
  private readonly onMensaje: (mensaje: MensajeSesionEnVivo) => void
  private readonly onReconectado: () => void
  private readonly onCambioEstado: (estado: EstadoCanal) => void
  private readonly crearWebSocket: WebSocketFactory
  private socket: WebSocket | null = null
  private cerradoPorLlamador = false
  private reconectando = false
  private backoffMs = BACKOFF_INICIAL_MS
  private timeoutReconexion: ReturnType<typeof setTimeout> | null = null

  constructor(
    sesionId: string,
    onMensaje: (mensaje: MensajeSesionEnVivo) => void,
    onReconectado: () => void,
    onCambioEstado: (estado: EstadoCanal) => void,
    crearWebSocket: WebSocketFactory = (url) => new WebSocket(url),
  ) {
    this.sesionId = sesionId
    this.onMensaje = onMensaje
    this.onReconectado = onReconectado
    this.onCambioEstado = onCambioEstado
    this.crearWebSocket = crearWebSocket
  }

  conectar(): void {
    const token = getSession()?.token ?? ""
    const url = `${urlBase()}/sesiones-en-vivo/${this.sesionId}/canal?token=${encodeURIComponent(token)}`
    const socket = this.crearWebSocket(url)
    this.socket = socket

    socket.onopen = () => {
      this.onCambioEstado("conectado")
      if (this.reconectando) {
        this.reconectando = false
        this.backoffMs = BACKOFF_INICIAL_MS
        this.onReconectado()
      }
    }

    socket.onmessage = (event: MessageEvent<string>) => {
      const mensaje = parsearMensaje(event.data)
      if (mensaje) {
        this.onMensaje(mensaje)
      }
    }

    socket.onclose = (event: CloseEvent) => {
      if (this.cerradoPorLlamador) return

      if (event.code === CODIGO_CIERRE_TOKEN_INVALIDO) {
        this.onCambioEstado("desconectado")
        clearSession()
        void router.navigate("/login")
        return
      }

      this.reconectando = true
      this.onCambioEstado("reconectando")
      this.timeoutReconexion = setTimeout(() => {
        this.conectar()
      }, this.backoffMs)
      this.backoffMs = Math.min(this.backoffMs * 2, BACKOFF_TOPE_MS)
    }
  }

  cerrar(): void {
    this.cerradoPorLlamador = true
    if (this.timeoutReconexion) {
      clearTimeout(this.timeoutReconexion)
      this.timeoutReconexion = null
    }
    this.socket?.close()
    this.onCambioEstado("desconectado")
  }
}

function parsearMensaje(data: string): MensajeSesionEnVivo | null {
  let bruto: Record<string, unknown>
  try {
    bruto = JSON.parse(data) as Record<string, unknown>
  } catch {
    return null
  }

  switch (bruto.tipo) {
    case "participantes_actualizados":
      return {
        tipo: "participantes_actualizados",
        cantidad: bruto.cantidad as number,
        participantes: (bruto.participantes as Record<string, unknown>[]).map((p) => ({
          estudianteId: p.estudianteId as string,
          nombre: p.nombre as string,
          unidoEn: p.unidoEn as string,
        })),
      }
    case "pregunta_presentada":
      return {
        tipo: "pregunta_presentada",
        preguntaActualIndice: bruto.preguntaActualIndice as number,
        pregunta: bruto.pregunta as PreguntaPresentada,
      }
    case "opciones_mostradas":
      return {
        tipo: "opciones_mostradas",
        preguntaActualIndice: bruto.preguntaActualIndice as number,
        opciones: bruto.opciones as string[] | null,
        tiempoLimitePorPreguntaSegundos: bruto.tiempoLimitePorPreguntaSegundos as number,
        cantidadRespuestas: bruto.cantidadRespuestas as number,
      }
    case "conteo_respuestas_actualizado":
      return {
        tipo: "conteo_respuestas_actualizado",
        preguntaActualIndice: bruto.preguntaActualIndice as number,
        cantidadRespuestas: bruto.cantidadRespuestas as number,
      }
    case "pregunta_cerrada":
      return {
        tipo: "pregunta_cerrada",
        preguntaActualIndice: bruto.preguntaActualIndice as number,
        respuestaCorrecta: bruto.respuestaCorrecta as RespuestaCorrectaCanal,
        distribucion: bruto.distribucion as OpcionDistribuidaCanal[],
        ranking: bruto.ranking as RankingItemCanal[],
      }
    case "sesion_finalizada":
      return {
        tipo: "sesion_finalizada",
        ranking: bruto.ranking as RankingItemCanal[],
      }
    default:
      return null
  }
}
