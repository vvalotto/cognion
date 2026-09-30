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
    expect(screen.getAllByText("Parcial 2")).toHaveLength(1)
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
