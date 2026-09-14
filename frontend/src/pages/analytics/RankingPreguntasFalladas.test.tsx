import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { RankingPreguntasFalladas } from "@/pages/analytics/RankingPreguntasFalladas"

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

function preguntaFallada(
  id: string,
  enunciado: string,
  unidad: string,
  tema: string,
  presentaciones: number,
  fallos: number,
) {
  return {
    pregunta_id: id,
    enunciado,
    unidad_tematica: unidad,
    tema,
    cantidad_presentaciones: presentaciones,
    cantidad_fallos: fallos,
    tasa_error: fallos / presentaciones,
  }
}

function renderPantalla() {
  return render(
    <MemoryRouter>
      <RankingPreguntasFalladas />
    </MemoryRouter>,
  )
}

describe("RankingPreguntasFalladas", () => {
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
      await screen.findByText("Elegí una materia para ver el ranking de preguntas más falladas."),
    ).toBeInTheDocument()
  })

  it("elegir Materia consulta toda la materia (sin comision_id) y muestra el listado numerado por posición", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver el ranking de preguntas más falladas.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          preguntaFallada("p1", "¿Qué es la inversión de dependencias?", "Unidad 3", "SOLID", 42, 24),
          preguntaFallada("p2", "¿Qué es el ciclo de vida del software?", "Unidad 1", "Fundamentos", 65, 6),
        ]),
      )

    await user.selectOptions(screen.getByLabelText("Materia"), "m1")

    expect(await screen.findByText("¿Qué es la inversión de dependencias?")).toBeInTheDocument()
    expect(screen.getByText("1.")).toBeInTheDocument()
    expect(screen.getByText("2.")).toBeInTheDocument()
    expect(screen.getByText("57%")).toBeInTheDocument()
    expect(screen.getByText("42 presentaciones · 24 fallos")).toBeInTheDocument()
    expect(screen.getByText("¿Qué es el ciclo de vida del software?")).toBeInTheDocument()
    expect(screen.getByText("9%")).toBeInTheDocument()

    const [urlRanking] = vi.mocked(fetch).mock.calls.at(-1) ?? []
    expect(String(urlRanking)).toBe(
      "http://localhost:8000/analytics/materias/m1/ranking-preguntas-falladas",
    )
  })

  it("elegir una Comisión puntual reconsulta con comision_id", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver el ranking de preguntas más falladas.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
      .mockResolvedValueOnce(jsonResponse(200, [preguntaFallada("p1", "Pregunta A", "U3", "Tema A", 10, 5)]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await screen.findByText("Pregunta A")

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [preguntaFallada("p2", "Pregunta B", "U2", "Tema B", 20, 2)]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")

    expect(await screen.findByText("Pregunta B")).toBeInTheDocument()
    const [url] = vi.mocked(fetch).mock.calls.at(-1) ?? []
    expect(String(url)).toBe(
      "http://localhost:8000/analytics/materias/m1/ranking-preguntas-falladas?comision_id=c1",
    )
  })

  it("color por severidad: alta (rojo) >= 50%, media (ámbar) 20-49%, baja (verde) < 20%", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver el ranking de preguntas más falladas.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          preguntaFallada("p1", "Pregunta alta", "U1", "Tema alto", 10, 6),
          preguntaFallada("p2", "Pregunta media", "U2", "Tema medio", 10, 3),
          preguntaFallada("p3", "Pregunta baja", "U3", "Tema bajo", 10, 1),
        ]),
      )
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await screen.findByText("Pregunta alta")

    expect(screen.getByText("60%")).toHaveClass("text-red-600")
    expect(screen.getByText("30%")).toHaveClass("text-amber-600")
    expect(screen.getByText("10%")).toHaveClass("text-emerald-700")
  })

  it("materia sin preguntas presentadas: muestra el estado vacío", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver el ranking de preguntas más falladas.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")

    expect(
      await screen.findByText("Esta materia todavía no tiene ninguna pregunta presentada."),
    ).toBeInTheDocument()
  })

  it("cambiar de Materia reinicia Comisión a 'Toda la materia' y reconsulta", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software"), materia("m2", "Gestión de Proyectos")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una materia para ver el ranking de preguntas más falladas.")

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
      .mockResolvedValueOnce(jsonResponse(200, [preguntaFallada("p1", "Pregunta A", "U1", "Tema A", 10, 5)]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await screen.findByText("Pregunta A")

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [preguntaFallada("p1", "Pregunta A", "U1", "Tema A", 10, 5)]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).toHaveValue("c1"))

    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [comision("c2", "Martes 18-20hs")]))
      .mockResolvedValueOnce(jsonResponse(200, [preguntaFallada("p2", "Pregunta B", "U2", "Tema B", 10, 1)]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m2")

    expect(await screen.findByText("Pregunta B")).toBeInTheDocument()
    expect(screen.getByLabelText("Comisión")).toHaveValue("")
  })
})
