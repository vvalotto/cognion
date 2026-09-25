import { act, cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
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

const navigateMock = vi.fn()
vi.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>()
  return { ...actual, useNavigate: () => navigateMock }
})

import { SalaEsperaDocente } from "@/pages/actividad-evaluativa/SalaEsperaDocente"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const estadoBase = {
  estado: "EnEspera",
  comision_id: "c1",
  cantidad_preguntas: 5,
  tiempo_limite_por_pregunta_segundos: 20,
  pregunta_actual_indice: null,
  opciones_mostradas: false,
  opciones_mostradas_en: null,
  pregunta_actual_cerrada: false,
  pregunta_actual: null,
  ya_respondio: null,
  puntaje_acumulado: null,
  total_participantes: 0,
  cantidad_respuestas: 0,
  resultado_pregunta: null,
}

const comision = {
  id: "c1",
  materia_id: "m1",
  horario: "Lunes 18-20hs",
  administrador_id: "a1",
  docentes_asignados: ["d1"],
}

const materias = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 10, activa: true },
]

function renderSala(sesionId = "s1") {
  return render(
    <MemoryRouter initialEntries={[`/sesiones-en-vivo/${sesionId}/sala`]}>
      <Routes>
        <Route path="/sesiones-en-vivo/:sesionId/sala" element={<SalaEsperaDocente />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("SalaEsperaDocente", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    hookState.estado = "conectado"
    navigateMock.mockClear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra los datos de la sesión sin participantes, con advertencia", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))

    renderSala()

    expect(await screen.findByText(/5 preguntas/)).toBeInTheDocument()
    expect(screen.getAllByText(/Todavía no se unió nadie/).length).toBeGreaterThan(0)
    expect(screen.getByRole("alert")).toHaveTextContent(/podés iniciar igual/)
  })

  it("inicia la sesión sin participantes igual, tras ver la advertencia", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(jsonResponse(200, { ...estadoBase, estado: "EnCurso" }))

    renderSala()
    await screen.findByRole("alert")

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }))

    expect(navigateMock).toHaveBeenCalledWith("/sesiones-en-vivo/s1/proyeccion")
  })

  it("los participantes aparecen en vivo por el canal, sin recargar", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))

    renderSala()
    await screen.findByText(/5 preguntas/)
    const llamadasAntes = vi.mocked(fetch).mock.calls.length

    act(() => {
      hookState.onMensaje({
        tipo: "participantes_actualizados",
        cantidad: 1,
        participantes: [{ estudianteId: "e1", nombre: "Ana Gómez", unidoEn: "2026-09-23T10:00:00Z" }],
      })
    })

    expect(await screen.findByText("Ana Gómez")).toBeInTheDocument()
    expect(vi.mocked(fetch).mock.calls.length).toBe(llamadasAntes)
  })

  it("inicia la sesión y navega a la proyección", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(
        jsonResponse(200, [{ estudiante_id: "e1", unido_en: "2026-09-23T10:00:00Z", nombre: "Ana Gómez" }]),
      )
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...estadoBase,
          estado: "EnCurso",
        }),
      )

    renderSala()
    await screen.findByText("Ana Gómez")

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }))

    expect(navigateMock).toHaveBeenCalledWith("/sesiones-en-vivo/s1/proyeccion")
  })

  it("422 SesionYaIniciada navega igual a la proyección (idempotencia)", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "La sesión ya fue iniciada" }), {
          status: 422,
          headers: { "Content-Type": "application/json" },
        }),
      )

    renderSala()
    await screen.findByText(/5 preguntas/)

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }))

    expect(navigateMock).toHaveBeenCalledWith("/sesiones-en-vivo/s1/proyeccion")
  })

  it("recuperar la sala con la sesión ya en curso redirige a la proyección", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, { ...estadoBase, estado: "EnCurso" }))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))

    renderSala()

    await vi.waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith("/sesiones-en-vivo/s1/proyeccion"),
    )
  })

  it("la sesión finalizada redirige al detalle de la Comisión", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, { ...estadoBase, estado: "Finalizada" }))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))

    renderSala()

    await vi.waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith("/actividad-evaluativa/comisiones/c1"),
    )
  })

  it("muestra el indicador Reconectando… y lo oculta al reconectar, recargando participantes", async () => {
    hookState.estado = "reconectando"
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))

    renderSala()
    await screen.findByText(/5 preguntas/)
    expect(screen.getByText("Reconectando…")).toBeInTheDocument()

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [{ estudiante_id: "e1", unido_en: "2026-09-23T10:00:00Z", nombre: "Ana Gómez" }]),
    )
    hookState.estado = "conectado"
    await act(async () => {
      hookState.onReconectado()
      await Promise.resolve()
    })

    expect(await screen.findByText("Ana Gómez")).toBeInTheDocument()
    expect(screen.queryByText("Reconectando…")).not.toBeInTheDocument()
  })
})
