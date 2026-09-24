import { act, cleanup, render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"

const hookState = vi.hoisted(() => ({
  onMensaje: (_mensaje: MensajeSesionEnVivo) => {},
  onReconectado: () => {},
  estado: "conectado" as "conectado" | "reconectando" | "desconectado",
}))

vi.mock("@/lib/use-canal-sesion-en-vivo", () => ({
  useCanalSesionEnVivo: (
    _sesionId: string,
    onMensaje: (mensaje: MensajeSesionEnVivo) => void,
    onReconectado: () => void,
  ) => {
    hookState.onMensaje = onMensaje
    hookState.onReconectado = onReconectado
    return hookState.estado
  },
}))

import { SesionEnVivoEstudiante } from "@/pages/actividad-evaluativa/SesionEnVivoEstudiante"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const participacion = { sesion_id: "s1", estudiante_id: "e1", unido_en: "2026-09-24T10:00:00+00:00" }

const estadoApi = (extra: Record<string, unknown> = {}) => ({
  estado: "en_espera",
  comision_id: "c1",
  cantidad_preguntas: 5,
  tiempo_limite_por_pregunta_segundos: 20,
  pregunta_actual_indice: null,
  opciones_mostradas: false,
  opciones_mostradas_en: null,
  pregunta_actual_cerrada: false,
  pregunta_actual: null,
  ya_respondio: false,
  puntaje_acumulado: 0,
  total_participantes: 3,
  cantidad_respuestas: 0,
  resultado_pregunta: null,
  ...extra,
})

function llamadasA(fragmento: string) {
  return vi.mocked(fetch).mock.calls.filter(([url]) => String(url).includes(fragmento))
}

function renderSesion() {
  return render(
    <MemoryRouter initialEntries={["/mis-sesiones-en-vivo/s1"]}>
      <Routes>
        <Route path="/mis-sesiones-en-vivo/:sesionId" element={<SesionEnVivoEstudiante />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("SesionEnVivoEstudiante", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    hookState.estado = "conectado"
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("al abrir se une y muestra la sala con la cantidad de participantes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()

    expect(await screen.findByRole("heading", { name: "¡Te uniste!" })).toBeInTheDocument()
    expect(screen.getByText("3 participantes")).toBeInTheDocument()
    expect(llamadasA("/sesiones-en-vivo/s1/unirse")).toHaveLength(1)
    // Primero se une, después pide el estado.
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain("/unirse")
  })

  it("el conteo de la sala es en vivo", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()
    await screen.findByText("3 participantes")

    act(() => {
      hookState.onMensaje({ tipo: "participantes_actualizados", cantidad: 4, participantes: [] })
    })
    expect(screen.getByText("4 participantes")).toBeInTheDocument()
  })

  it("pasa solo a la pregunta cuando el Docente inicia", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()
    await screen.findByRole("heading", { name: "¡Te uniste!" })

    act(() => {
      hookState.onMensaje({
        tipo: "pregunta_presentada",
        preguntaActualIndice: 0,
        pregunta: { preguntaId: "p1", enunciado: "¿Qué es SOLID?", tipo: "opcion_multiple" },
      })
    })
    expect(screen.queryByRole("heading", { name: "¡Te uniste!" })).not.toBeInTheDocument()
    expect(screen.getByText(/en curso/)).toBeInTheDocument()
  })

  it("unión tardía a una sesión en curso entra a la etapa de la pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ estado: "en_curso", pregunta_actual_indice: 1 })))

    renderSesion()

    expect(await screen.findByText(/en curso/)).toBeInTheDocument()
    expect(screen.queryByRole("heading", { name: "¡Te uniste!" })).not.toBeInTheDocument()
  })

  it("recargar vuelve a la sala: se une de nuevo (idempotente) sin guardar nada en el cliente", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ total_participantes: 5 })))

    const { unmount } = renderSesion()
    await screen.findByText("3 participantes")
    unmount()

    renderSesion()
    expect(await screen.findByText("5 participantes")).toBeInTheDocument()
    expect(llamadasA("/unirse")).toHaveLength(2)
  })

  it("una sesión ya finalizada (422 al unirse) no corta: el estado lleva al final", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(422, { detail: "SesionYaFinalizada" }))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ estado: "finalizada" })))

    renderSesion()

    expect(await screen.findByText(/finalizó/)).toBeInTheDocument()
  })

  it("una sesión que no existe (404) avisa y ofrece volver", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(404, { detail: "SesionNoEncontrada" }))

    renderSesion()

    expect(await screen.findByRole("alert")).toHaveTextContent("Esta sesión ya no está disponible.")
    expect(screen.getByRole("link", { name: /Volver a mis materias/ })).toHaveAttribute(
      "href",
      "/mis-actividades/materias",
    )
    expect(llamadasA("/sesiones-en-vivo/s1")).toHaveLength(1)
  })

  it("si el estado da 404 también avisa", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(404, { detail: "SesionNoEncontrada" }))

    renderSesion()

    expect(await screen.findByRole("alert")).toHaveTextContent("Esta sesión ya no está disponible.")
  })

  it("el final llega por el canal", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ estado: "en_curso" })))

    renderSesion()
    await screen.findByText(/en curso/)

    act(() => {
      hookState.onMensaje({ tipo: "sesion_finalizada", ranking: [] })
    })
    expect(screen.getByText(/finalizó/)).toBeInTheDocument()
  })

  it("al reconectar recalcula la etapa y el conteo desde el servidor, con el chip de conexión", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ total_participantes: 8 })))

    hookState.estado = "reconectando"
    renderSesion()
    await screen.findByText("3 participantes")
    expect(screen.getByText("Reconectando…")).toBeInTheDocument()

    await act(async () => {
      hookState.onReconectado()
    })
    await waitFor(() => expect(screen.getByText("8 participantes")).toBeInTheDocument())
  })

  it("los mensajes que llegan antes del estado se ignoran", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()
    act(() => {
      hookState.onMensaje({ tipo: "participantes_actualizados", cantidad: 9, participantes: [] })
    })

    expect(await screen.findByText("3 participantes")).toBeInTheDocument()
  })
})
