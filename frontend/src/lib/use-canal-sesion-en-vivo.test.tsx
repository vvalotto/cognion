import { act, render } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"
import { setSession } from "@/lib/session"
import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"

class WebSocketFalso {
  static instancias: WebSocketFalso[] = []
  url: string
  cerrado = false
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent<string>) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null

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

const FACTORY: (url: string) => WebSocket = (url) => new WebSocketFalso(url) as unknown as WebSocket

function Componente({
  onMensaje,
  onReconectado,
}: {
  onMensaje: (m: MensajeSesionEnVivo) => void
  onReconectado: () => void
}) {
  const estado = useCanalSesionEnVivo("s1", onMensaje, onReconectado, FACTORY)
  return <p>estado: {estado}</p>
}

describe("useCanalSesionEnVivo", () => {
  beforeEach(() => {
    localStorage.clear()
    WebSocketFalso.instancias = []
    setSession({ token: "jwt-de-prueba", rol: "docente" })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("crea el canal dentro de useEffect, no en el render", () => {
    render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)

    expect(WebSocketFalso.instancias).toHaveLength(1)
  })

  it("sobrevive al doble montaje de StrictMode sin crear sockets huérfanos", () => {
    const { unmount } = render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)
    unmount()
    render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)

    expect(WebSocketFalso.instancias.filter((s) => !s.cerrado)).toHaveLength(1)
  })

  it("el cleanup cierra el socket al desmontar", () => {
    const { unmount } = render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)
    const socket = WebSocketFalso.instancias[0]

    act(() => {
      unmount()
    })

    expect(socket.cerrado).toBe(true)
  })

  it("propaga un mensaje recibido al callback más reciente", () => {
    const onMensaje = vi.fn()
    render(<Componente onMensaje={onMensaje} onReconectado={vi.fn()} />)
    const socket = WebSocketFalso.instancias[0]

    act(() => {
      socket.simularMensaje({ tipo: "sesion_finalizada", ranking: [] })
    })

    expect(onMensaje).toHaveBeenCalledWith({ tipo: "sesion_finalizada", ranking: [] })
  })

  it("propaga la reconexión al callback más reciente", () => {
    vi.useFakeTimers()
    const onReconectado = vi.fn()
    render(<Componente onMensaje={vi.fn()} onReconectado={onReconectado} />)
    const primerSocket = WebSocketFalso.instancias[0]

    act(() => {
      primerSocket.simularCierre(1006)
    })
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    act(() => {
      WebSocketFalso.instancias[1]?.simularApertura()
    })

    expect(onReconectado).toHaveBeenCalledTimes(1)
    vi.useRealTimers()
  })
})
