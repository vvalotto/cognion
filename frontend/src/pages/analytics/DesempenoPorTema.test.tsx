import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { DesempenoPorTema } from "@/pages/analytics/DesempenoPorTema"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function materia(id: string, nombre: string) {
  return { id, nombre, banco_id: `b-${id}`, cantidad_preguntas_activas: 10 }
}

function comision(id: string, horario: string) {
  return { id, horario }
}

function tasaTema(unidad: string, tema: string, respuestas: number, incorrectas: number) {
  return {
    unidad_tematica: unidad,
    tema,
    cantidad_respuestas: respuestas,
    cantidad_incorrectas: incorrectas,
    tasa_error: incorrectas / respuestas,
  }
}

function renderPantalla() {
  return render(
    <MemoryRouter>
      <DesempenoPorTema />
    </MemoryRouter>,
  )
}

describe("DesempenoPorTema", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("estado inicial: placeholder sin listado", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )

    renderPantalla()

    expect(
      await screen.findByText("Elegí una materia para ver la tasa de error por tema."),
    ).toBeInTheDocument()
  })

  it("elegir Materia consulta toda la materia (sin comision_id) y muestra el listado ordenado", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver la tasa de error por tema.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          tasaTema("Unidad 3 — Principios SOLID", "Inversión de dependencias", 42, 24),
          tasaTema("Unidad 1 — Fundamentos", "Ciclo de vida del software", 65, 6),
        ]),
      )

    await user.selectOptions(screen.getByLabelText("Materia"), "m1")

    expect(await screen.findByText("Inversión de dependencias")).toBeInTheDocument()
    expect(screen.getByText("57%")).toBeInTheDocument()
    expect(screen.getByText("42 respuestas · 24 incorrectas")).toBeInTheDocument()
    expect(screen.getByText("Ciclo de vida del software")).toBeInTheDocument()
    expect(screen.getByText("9%")).toBeInTheDocument()

    const [urlTasas] = vi.mocked(fetch).mock.calls.at(-1) ?? []
    expect(String(urlTasas)).toBe(
      "http://localhost:8000/analytics/materias/m1/tasa-error-por-tema",
    )
  })

  it("elegir una Comisión puntual reconsulta con comision_id", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver la tasa de error por tema.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
      .mockResolvedValueOnce(
        jsonResponse(200, [tasaTema("Unidad 3", "Tema A", 10, 5)]),
      )
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await screen.findByText("Tema A")

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [tasaTema("Unidad 2", "Tema B", 20, 2)]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")

    expect(await screen.findByText("Tema B")).toBeInTheDocument()
    const [url] = vi.mocked(fetch).mock.calls.at(-1) ?? []
    expect(String(url)).toBe(
      "http://localhost:8000/analytics/materias/m1/tasa-error-por-tema?comision_id=c1",
    )
  })

  it("color por severidad: alta (rojo) >= 50%, media (ámbar) 20-49%, baja (verde) < 20%", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver la tasa de error por tema.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          tasaTema("U1", "Tema alto", 10, 6),
          tasaTema("U2", "Tema medio", 10, 3),
          tasaTema("U3", "Tema bajo", 10, 1),
        ]),
      )
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await screen.findByText("Tema alto")

    expect(screen.getByText("60%")).toHaveClass("text-red-600")
    expect(screen.getByText("30%")).toHaveClass("text-amber-600")
    expect(screen.getByText("10%")).toHaveClass("text-emerald-700")
  })

  it("materia sin evaluaciones finalizadas: muestra el estado vacío", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver la tasa de error por tema.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")

    expect(
      await screen.findByText("Esta materia todavía no tiene ninguna evaluación finalizada."),
    ).toBeInTheDocument()
  })

  it("cambiar de Materia reinicia Comisión a 'Toda la materia' y reconsulta", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software"), materia("m2", "Gestión de Proyectos")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver la tasa de error por tema.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
      .mockResolvedValueOnce(jsonResponse(200, [tasaTema("U1", "Tema A", 10, 5)]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await screen.findByText("Tema A")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [tasaTema("U1", "Tema A", 10, 5)]))
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).toHaveValue("c1"))

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c2", "Martes 18-20hs")]))
      .mockResolvedValueOnce(jsonResponse(200, [tasaTema("U2", "Tema B", 10, 1)]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m2")

    expect(await screen.findByText("Tema B")).toBeInTheDocument()
    expect(screen.getByLabelText("Comisión")).toHaveValue("")
  })
})
