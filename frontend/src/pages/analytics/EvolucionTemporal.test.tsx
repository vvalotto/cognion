import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { EvolucionTemporal } from "@/pages/analytics/EvolucionTemporal"

const MATERIA_ID = "m1"
const COMISION_ID = "c1"
const ESTUDIANTE_ID = "u1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function puntoEstudiante(actividadId: string, titulo: string, finalizadaEn: string, porcentaje: number) {
  return {
    actividad_id: actividadId,
    titulo_actividad: titulo,
    finalizada_en: finalizadaEn,
    porcentaje_acierto: porcentaje,
  }
}

function puntoComision(actividadId: string, titulo: string, promedio: number) {
  return { actividad_id: actividadId, titulo_actividad: titulo, porcentaje_aciertos_promedio: promedio }
}

function renderPantalla() {
  return render(
    <MemoryRouter
      initialEntries={[
        `/analytics/desempeno-por-comision/materias/${MATERIA_ID}/comisiones/${COMISION_ID}/estudiantes/${ESTUDIANTE_ID}/evolucion`,
      ]}
    >
      <Routes>
        <Route
          path="/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evolucion"
          element={<EvolucionTemporal />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EvolucionTemporal", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("serie completa: dibuja el gráfico con las etiquetas de ambas series", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [
          puntoEstudiante("a1", "Parcial 1", "2026-08-01T00:00:00Z", 80),
          puntoEstudiante("a2", "Parcial 2", "2026-08-15T00:00:00Z", 60),
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          puntoComision("a1", "Parcial 1", 70),
          puntoComision("a2", "Parcial 2", 65),
        ]),
      )

    renderPantalla()

    expect(await screen.findByRole("img", { name: /evolución temporal/i })).toBeInTheDocument()
    expect(screen.getAllByText("Parcial 1").length).toBeGreaterThan(0)
    expect(screen.getAllByText("Parcial 2").length).toBeGreaterThan(0)
    expect(screen.getByText("Estudiante")).toBeInTheDocument()
    expect(screen.getByText("Promedio de la comisión")).toBeInTheDocument()
  })

  it("una sola evaluación: dibuja un solo punto sin polyline", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [puntoEstudiante("a1", "Parcial 1", "2026-08-01T00:00:00Z", 80)]),
      )
      .mockResolvedValueOnce(jsonResponse(200, [puntoComision("a1", "Parcial 1", 70)]))

    renderPantalla()

    const svg = await screen.findByRole("img", { name: /evolución temporal/i })
    expect(svg.querySelectorAll("polyline")).toHaveLength(0)
    expect(svg.querySelectorAll("circle")).toHaveLength(2)
  })

  it("una sola actividad con título largo: la etiqueta del eje no se trunca", async () => {
    const titulo = "Parcial numero 1 de Ingeniería"
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [puntoEstudiante("a1", titulo, "2026-08-01T00:00:00Z", 67)]),
      )
      .mockResolvedValueOnce(jsonResponse(200, [puntoComision("a1", titulo, 67)]))

    renderPantalla()

    await screen.findByRole("img", { name: /evolución temporal/i })
    expect(screen.getAllByText(titulo).length).toBeGreaterThan(0)
    expect(screen.queryByText(/…$/)).not.toBeInTheDocument()
  })

  it("muchas actividades con títulos largos: acorta la etiqueta y deja el título completo en el tooltip", async () => {
    const titulos = Array.from({ length: 10 }, (_, i) => `Evaluación integradora número ${i + 1}`)
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          titulos.map((t, i) => puntoEstudiante(`a${i}`, t, `2026-08-${10 + i}T00:00:00Z`, 50)),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, titulos.map((t, i) => puntoComision(`a${i}`, t, 60))))

    renderPantalla()

    const svg = await screen.findByRole("img", { name: /evolución temporal/i })
    const etiquetas = Array.from(svg.querySelectorAll("text")).filter((t) => t.textContent?.includes("…"))
    expect(etiquetas.length).toBe(10)
    expect(svg.querySelector("title")?.textContent).toBe(titulos[0])
  })

  it("las etiquetas de los extremos no se salen del gráfico aunque el título sea largo", async () => {
    const titulos = [
      "Evaluación integradora número uno de la unidad",
      "Parcial 2",
      "Evaluación integradora número tres de la unidad",
    ]
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          titulos.map((t, i) => puntoEstudiante(`a${i}`, t, `2026-08-${10 + i}T00:00:00Z`, 50)),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, titulos.map((t, i) => puntoComision(`a${i}`, t, 60))))

    renderPantalla()

    const svg = await screen.findByRole("img", { name: /evolución temporal/i })
    const ancho = Number(svg.getAttribute("viewBox")?.split(" ")[2])
    const etiquetas = Array.from(svg.querySelectorAll("text")).filter(
      (t) => t.getAttribute("text-anchor") === "middle",
    )
    expect(etiquetas.length).toBe(3)
    for (const t of etiquetas) {
      const visible = Array.from(t.childNodes)
        .filter((n) => n.nodeType === Node.TEXT_NODE)
        .map((n) => n.textContent ?? "")
        .join("")
      const mitad = (visible.length * 5.5) / 2
      const x = Number(t.getAttribute("x"))
      expect(x - mitad).toBeGreaterThanOrEqual(0)
      expect(x + mitad).toBeLessThanOrEqual(ancho)
    }
  })

  it("con un solo dato, el promedio de la comisión se dibuja como anillo visible aunque coincida", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [puntoEstudiante("a1", "Parcial 1", "2026-08-01T00:00:00Z", 67)]),
      )
      .mockResolvedValueOnce(jsonResponse(200, [puntoComision("a1", "Parcial 1", 67)]))

    renderPantalla()

    const svg = await screen.findByRole("img", { name: /evolución temporal/i })
    const circulos = Array.from(svg.querySelectorAll("circle"))
    expect(circulos.some((c) => c.getAttribute("fill") === "none" && c.getAttribute("r") === "7")).toBe(true)
    expect(circulos.some((c) => c.getAttribute("fill") === "#1d75b5" && c.getAttribute("r") === "4")).toBe(true)
  })

  it("actividad no rendida por el estudiante: no aparece en la serie del estudiante", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [puntoEstudiante("a1", "Parcial 1", "2026-08-01T00:00:00Z", 80)]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          puntoComision("a1", "Parcial 1", 70),
          puntoComision("a2", "Parcial 2", 65),
        ]),
      )

    renderPantalla()

    const svg = await screen.findByRole("img", { name: /evolución temporal/i })
    // 1 punto de estudiante + 2 de comisión = 3 círculos, sin duplicar el eje X (2 actividades)
    expect(svg.querySelectorAll("circle")).toHaveLength(3)
    const titulosDelEje = Array.from(svg.querySelectorAll("title")).map((t) => t.textContent)
    expect(titulosDelEje.filter((t) => t === "Parcial 2")).toHaveLength(1)
  })

  it("sin ninguna evaluación finalizada: muestra el estado vacío, sin gráfico", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [])).mockResolvedValueOnce(
      jsonResponse(200, []),
    )

    renderPantalla()

    expect(
      await screen.findByText("Ni el estudiante ni la comisión tienen evaluaciones finalizadas todavía."),
    ).toBeInTheDocument()
    expect(screen.queryByRole("img")).not.toBeInTheDocument()
  })

  it("error de red: muestra el mensaje de error", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("network error"))

    renderPantalla()

    expect(
      await screen.findByText("No se pudo cargar la evolución temporal. Intentá de nuevo más tarde."),
    ).toBeInTheDocument()
  })
})
