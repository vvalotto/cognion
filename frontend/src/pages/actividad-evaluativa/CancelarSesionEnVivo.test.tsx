import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const navigateMock = vi.fn()
vi.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>()
  return { ...actual, useNavigate: () => navigateMock }
})

import { CancelarSesionEnVivo } from "@/pages/actividad-evaluativa/CancelarSesionEnVivo"
import { MATERIAS_TEST } from "@/test/fetch-con-materias"

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
}

const estado = {
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
  total_participantes: 2,
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

const participantes = [
  { estudiante_id: "e1", unido_en: "2026-09-27T10:00:00Z", nombre: "Ana Gómez" },
  { estudiante_id: "e2", unido_en: "2026-09-27T10:01:00Z", nombre: "Juan Pérez" },
]

/** Responde por URL; `cancelar` es la respuesta del `POST .../cancelar`. */
function mockFetch(cancelar: Response = json(200, {})) {
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const url = String(input)
    if (init?.method === "POST" && url.endsWith("/sesiones-en-vivo/s1/cancelar")) return cancelar
    if (url.endsWith("/sesiones-en-vivo/s1")) return json(200, estado)
    if (url.endsWith("/sesiones-en-vivo/s1/participantes")) return json(200, participantes)
    if (url.endsWith("/comisiones/c1")) return json(200, comision)
    if (/\/materias(\?[^/]*)?$/.test(url)) return json(200, MATERIAS_TEST)
    throw new Error(`fetch inesperado: ${url}`)
  })
}

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/sesiones-en-vivo/s1/cancelar"]}>
      <Routes>
        <Route path="/sesiones-en-vivo/:sesionId/cancelar" element={<CancelarSesionEnVivo />} />
      </Routes>
    </MemoryRouter>,
  )
}

function llamadasPost() {
  return vi.mocked(fetch).mock.calls.filter(([, init]) => (init as RequestInit)?.method === "POST")
}

describe("CancelarSesionEnVivo (US-ADJ-58)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    navigateMock.mockClear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el resumen de la sesión y el aviso a la sala", async () => {
    mockFetch()
    renderPantalla()

    expect(await screen.findByRole("heading", { name: "¿Cancelar esta sesión?" })).toBeInTheDocument()
    expect(await screen.findByText("5 · Ingeniería de Software")).toBeInTheDocument()
    expect(await screen.findByText("2")).toBeInTheDocument()
    expect(screen.getByRole("note")).toHaveTextContent(/ven que la sesión se canceló/)
  })

  it("al confirmar cancela y vuelve al detalle de la Comisión", async () => {
    mockFetch()
    renderPantalla()
    const user = userEvent.setup()

    await user.click(await screen.findByRole("button", { name: "Cancelar sesión" }))

    await vi.waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith("/actividad-evaluativa/comisiones/c1"),
    )
    expect(llamadasPost()).toHaveLength(1)
  })

  it("'Volver a la sala' no toca la sesión", async () => {
    mockFetch()
    renderPantalla()
    const user = userEvent.setup()

    await user.click(await screen.findByRole("button", { name: "Volver a la sala" }))

    expect(navigateMock).toHaveBeenCalledWith("/sesiones-en-vivo/s1/sala")
    expect(llamadasPost()).toHaveLength(0)
  })

  it("422 (ya iniciada o ya cancelada) muestra el error sin navegar", async () => {
    mockFetch(json(422, { detail: "La sesión en vivo 's1' ya fue iniciada." }))
    renderPantalla()
    const user = userEvent.setup()

    await user.click(await screen.findByRole("button", { name: "Cancelar sesión" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/ya no se puede cancelar/)
    expect(navigateMock).not.toHaveBeenCalled()
    expect(screen.getByRole("button", { name: "Cancelar sesión" })).toBeEnabled()
  })
})
