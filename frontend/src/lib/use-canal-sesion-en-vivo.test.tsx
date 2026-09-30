import { act, cleanup, render } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { RESINCRONIZAR_CADA_MS, useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"
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
    // Sin desmontar, los componentes de tests anteriores seguirían escuchando visibilitychange.
    cleanup()
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

  describe("resincronización (hallazgo #7, Safari iOS)", () => {
    function visibilidad(valor: DocumentVisibilityState) {
      vi.spyOn(document, "visibilityState", "get").mockReturnValue(valor)
    }

    afterEach(() => {
      vi.useRealTimers()
    })

    it("al volver la pestaña a primer plano rearma la conexión", () => {
      render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)
      WebSocketFalso.instancias[0].simularApertura()

      visibilidad("visible")
      act(() => {
        document.dispatchEvent(new Event("visibilitychange"))
      })

      expect(WebSocketFalso.instancias).toHaveLength(2)
      expect(WebSocketFalso.instancias[0].cerrado).toBe(true)
    })

    it("pageshow y online también rearman, sin repetir si llegan juntos", () => {
      render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)
      visibilidad("visible")
      act(() => {
        window.dispatchEvent(new Event("pageshow"))
        window.dispatchEvent(new Event("online"))
      })

      expect(WebSocketFalso.instancias).toHaveLength(2)
    })

    it("al ocultarse la pestaña no rearma", () => {
      render(<Componente onMensaje={vi.fn()} onReconectado={vi.fn()} />)
      visibilidad("hidden")
      act(() => {
        document.dispatchEvent(new Event("visibilitychange"))
      })

      expect(WebSocketFalso.instancias).toHaveLength(1)
    })

    it("resincroniza cada 10 s con la pantalla visible, y no con la pestaña oculta", () => {
      vi.useFakeTimers()
      const onReconectado = vi.fn()
      render(<Componente onMensaje={vi.fn()} onReconectado={onReconectado} />)

      visibilidad("visible")
      act(() => {
        vi.advanceTimersByTime(RESINCRONIZAR_CADA_MS)
      })
      expect(onReconectado).toHaveBeenCalledTimes(1)

      visibilidad("hidden")
      act(() => {
        vi.advanceTimersByTime(RESINCRONIZAR_CADA_MS * 3)
      })
      expect(onReconectado).toHaveBeenCalledTimes(1)
    })

    it("al desmontar deja de escuchar y de resincronizar", () => {
      vi.useFakeTimers()
      const onReconectado = vi.fn()
      const { unmount } = render(<Componente onMensaje={vi.fn()} onReconectado={onReconectado} />)
      unmount()

      visibilidad("visible")
      act(() => {
        document.dispatchEvent(new Event("visibilitychange"))
        vi.advanceTimersByTime(RESINCRONIZAR_CADA_MS * 2)
      })
      expect(WebSocketFalso.instancias).toHaveLength(1)
      expect(onReconectado).not.toHaveBeenCalled()
    })
  })
})

