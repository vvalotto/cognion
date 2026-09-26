import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock("@/router", () => ({
  router: { navigate: navigateMock },
}))

import { CanalSesionEnVivo, type MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import { getSession, setSession } from "@/lib/session"

/** `WebSocket` falso inyectable — `jsdom` no trae uno funcional. */
class WebSocketFalso {
  static instancias: WebSocketFalso[] = []
  url: string
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent<string>) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  cerrado = false

  constructor(url: string) {
    this.url = url
    WebSocketFalso.instancias.push(this)
  }

  close(): void {
    this.cerrado = true
  }

  simularApertura(): void {
    this.onopen?.()
  }

  simularMensaje(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent<string>)
  }

  simularCierre(code: number): void {
    this.onclose?.({ code } as CloseEvent)
  }
}

function crearFactory(): (url: string) => WebSocket {
  return (url: string) => new WebSocketFalso(url) as unknown as WebSocket
}

describe("CanalSesionEnVivo", () => {
  beforeEach(() => {
    localStorage.clear()
    WebSocketFalso.instancias = []
    navigateMock.mockClear()
    setSession({ token: "jwt-de-prueba", rol: "docente" })
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("recibe y tipa un mensaje pregunta_cerrada en camelCase", () => {
    const mensajes: MensajeSesionEnVivo[] = []
    const canal = new CanalSesionEnVivo(
      "s1",
      (m) => mensajes.push(m),
      vi.fn(),
      vi.fn(),
      crearFactory(),
    )
    canal.conectar()
    const socket = WebSocketFalso.instancias[0]
    socket.simularApertura()

    // Formato real del backend (snake_case), no el del cliente.
    socket.simularMensaje({
      tipo: "pregunta_cerrada",
      pregunta_actual_indice: 0,
      respuesta_correcta: { contenido: { opcion_indice: 1 }, texto: "b", opciones: ["a", "b"] },
      distribucion: [{ opcion: "1", cantidad: 3 }],
      ranking: [{ posicion: 1, estudiante_id: "e1", nombre: "Ana", puntaje_acumulado: 950 }],
    })

    expect(mensajes).toHaveLength(1)
    expect(mensajes[0]).toEqual({
      tipo: "pregunta_cerrada",
      preguntaActualIndice: 0,
      respuestaCorrecta: { contenido: { opcion_indice: 1 }, texto: "b", opciones: ["a", "b"] },
      distribucion: [{ opcion: "1", cantidad: 3 }],
      ranking: [{ posicion: 1, estudianteId: "e1", nombre: "Ana", puntajeAcumulado: 950 }],
    })
  })

  it("se reconecta tras un corte y dispara onReconectado, el estado vuelve a conectado", () => {
    const onReconectado = vi.fn()
    const estados: string[] = []
    const canal = new CanalSesionEnVivo("s1", vi.fn(), onReconectado, (e) => estados.push(e), crearFactory())
    canal.conectar()
    WebSocketFalso.instancias[0].simularApertura()
    expect(estados.at(-1)).toBe("conectado")

    WebSocketFalso.instancias[0].simularCierre(1006)
    expect(estados.at(-1)).toBe("reconectando")
    expect(onReconectado).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1000)
    expect(WebSocketFalso.instancias).toHaveLength(2)
    WebSocketFalso.instancias[1].simularApertura()

    expect(onReconectado).toHaveBeenCalledTimes(1)
    expect(estados.at(-1)).toBe("conectado")
  })

  it("el backoff es exponencial con tope de 10 segundos", () => {
    const canal = new CanalSesionEnVivo("s1", vi.fn(), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()

    const intervalosEsperados = [1000, 2000, 4000, 8000, 10000, 10000]
    for (const intervalo of intervalosEsperados) {
      const cantidadPrevia = WebSocketFalso.instancias.length
      WebSocketFalso.instancias.at(-1)!.simularCierre(1006)
      vi.advanceTimersByTime(intervalo - 1)
      expect(WebSocketFalso.instancias).toHaveLength(cantidadPrevia)
      vi.advanceTimersByTime(1)
      expect(WebSocketFalso.instancias).toHaveLength(cantidadPrevia + 1)
    }
  })

  it("un cierre 1008 no reintenta, limpia la sesión y navega a /login", () => {
    const canal = new CanalSesionEnVivo("s1", vi.fn(), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    WebSocketFalso.instancias[0].simularCierre(1008)

    expect(getSession()).toBeNull()
    expect(navigateMock).toHaveBeenCalledWith("/login")

    vi.advanceTimersByTime(15000)
    expect(WebSocketFalso.instancias).toHaveLength(1)
  })

  it("tipa los mensajes participantes_actualizados, pregunta_presentada, opciones_mostradas y conteo_respuestas_actualizado", () => {
    const mensajes: MensajeSesionEnVivo[] = []
    const canal = new CanalSesionEnVivo("s1", (m) => mensajes.push(m), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    const socket = WebSocketFalso.instancias[0]

    socket.simularMensaje({
      tipo: "participantes_actualizados",
      cantidad: 1,
      participantes: [{ estudiante_id: "e1", nombre: "Ana", unido_en: "2026-09-22T10:00:00Z" }],
    })
    socket.simularMensaje({
      tipo: "pregunta_presentada",
      pregunta_actual_indice: 0,
      pregunta: { pregunta_id: "p1", enunciado: "¿SOLID?", tipo: "opcion_multiple" },
    })
    socket.simularMensaje({
      tipo: "opciones_mostradas",
      pregunta_actual_indice: 0,
      opciones: ["a", "b"],
      tiempo_limite_por_pregunta_segundos: 20,
      cantidad_respuestas: 0,
    })
    socket.simularMensaje({
      tipo: "conteo_respuestas_actualizado",
      pregunta_actual_indice: 0,
      cantidad_respuestas: 2,
    })
    socket.simularMensaje({
      tipo: "sesion_finalizada",
      ranking: [{ posicion: 1, estudiante_id: "e1", nombre: "Ana", puntaje_acumulado: 950 }],
    })

    // El backend manda snake_case (hallazgo UAT E2E US-6.3.10); el cliente recibe camelCase.
    expect(mensajes).toEqual([
      {
        tipo: "participantes_actualizados",
        cantidad: 1,
        participantes: [{ estudianteId: "e1", nombre: "Ana", unidoEn: "2026-09-22T10:00:00Z" }],
      },
      {
        tipo: "pregunta_presentada",
        preguntaActualIndice: 0,
        pregunta: { preguntaId: "p1", enunciado: "¿SOLID?", tipo: "opcion_multiple" },
      },
      {
        tipo: "opciones_mostradas",
        preguntaActualIndice: 0,
        opciones: ["a", "b"],
        tiempoLimitePorPreguntaSegundos: 20,
        cantidadRespuestas: 0,
      },
      { tipo: "conteo_respuestas_actualizado", preguntaActualIndice: 0, cantidadRespuestas: 2 },
      {
        tipo: "sesion_finalizada",
        ranking: [{ posicion: 1, estudianteId: "e1", nombre: "Ana", puntajeAcumulado: 950 }],
      },
    ])
  })

  it("un mensaje que no es JSON válido se ignora sin romper", () => {
    const mensajes: MensajeSesionEnVivo[] = []
    const canal = new CanalSesionEnVivo("s1", (m) => mensajes.push(m), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    const socket = WebSocketFalso.instancias[0]

    socket.onmessage?.({ data: "esto no es json" } as MessageEvent<string>)
    socket.simularMensaje({ tipo: "sesion_finalizada", ranking: [] })

    expect(mensajes).toEqual([{ tipo: "sesion_finalizada", ranking: [] }])
  })

  it("un mensaje con tipo desconocido se ignora y los siguientes se procesan", () => {
    const mensajes: MensajeSesionEnVivo[] = []
    const canal = new CanalSesionEnVivo("s1", (m) => mensajes.push(m), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    const socket = WebSocketFalso.instancias[0]

    socket.simularMensaje({ tipo: "tipo_futuro_desconocido", campo: 1 })
    socket.simularMensaje({ tipo: "sesion_finalizada", ranking: [] })

    expect(mensajes).toEqual([{ tipo: "sesion_finalizada", ranking: [] }])
  })

  it("cerrar() cierra el socket y no reintenta", () => {
    const canal = new CanalSesionEnVivo("s1", vi.fn(), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    const socket = WebSocketFalso.instancias[0]

    canal.cerrar()
    socket.simularCierre(1006)

    expect(socket.cerrado).toBe(true)
    vi.advanceTimersByTime(15000)
    expect(WebSocketFalso.instancias).toHaveLength(1)
  })

  it("reconectarAhora descarta el socket actual (aunque parezca abierto) y avisa al reabrir", () => {
    const onReconectado = vi.fn()
    const estados: string[] = []
    const canal = new CanalSesionEnVivo("s1", vi.fn(), onReconectado, (e) => estados.push(e), crearFactory())
    canal.conectar()
    const zombi = WebSocketFalso.instancias[0]
    zombi.simularApertura()

    canal.reconectarAhora()

    expect(zombi.cerrado).toBe(true)
    expect(zombi.onclose).toBeNull()
    expect(WebSocketFalso.instancias).toHaveLength(2)
    expect(estados.at(-1)).toBe("reconectando")
    WebSocketFalso.instancias[1].simularApertura()
    expect(onReconectado).toHaveBeenCalledTimes(1)
    expect(estados.at(-1)).toBe("conectado")
  })

  it("reconectarAhora cancela una reconexión pendiente y no duplica sockets", () => {
    const canal = new CanalSesionEnVivo("s1", vi.fn(), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    WebSocketFalso.instancias[0].simularCierre(1006)
    canal.reconectarAhora()
    vi.advanceTimersByTime(20_000)

    expect(WebSocketFalso.instancias).toHaveLength(2)
  })

  it("reconectarAhora no hace nada después de cerrar el canal", () => {
    const canal = new CanalSesionEnVivo("s1", vi.fn(), vi.fn(), vi.fn(), crearFactory())
    canal.conectar()
    canal.cerrar()
    canal.reconectarAhora()

    expect(WebSocketFalso.instancias).toHaveLength(1)
  })
})

