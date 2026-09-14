import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { DesempenoPorComisionDetalleEstudiante } from "@/pages/analytics/DesempenoPorComisionDetalleEstudiante"

const MATERIA_ID = "m1"
const COMISION_ID = "c1"
const ESTUDIANTE_ID = "u1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function desempeno(evaluaciones: unknown[], resumen: Record<string, number>) {
  return { evaluaciones, resumen }
}

function evaluacionDetalle(
  actividadId: string,
  finalizadaEn: string,
  correctas: number,
  incorrectas: number,
) {
  return {
    evaluacion_id: `ev-${actividadId}`,
    actividad_id: actividadId,
    finalizada_en: finalizadaEn,
    cantidad_correctas: correctas,
    cantidad_incorrectas: incorrectas,
  }
}

function actividadResumen(id: string, materiaId: string, titulo: string) {
  return {
    id,
    materia_id: materiaId,
    titulo,
    fecha_apertura: "2026-08-01T00:00:00+00:00",
    fecha_cierre: "2026-09-01T00:00:00+00:00",
    cantidad_preguntas: 10,
    cantidad_intentos_permitidos: 1,
    estado: "abierta",
    cerrada_manualmente: false,
    cantidad_evaluaciones_activas: 0,
    cantidad_evaluaciones_finalizadas: 1,
  }
}

function renderPantalla() {
  return render(
    <MemoryRouter
      initialEntries={[
        `/analytics/desempeno-por-comision/materias/${MATERIA_ID}/comisiones/${COMISION_ID}/estudiantes/${ESTUDIANTE_ID}`,
      ]}
    >
      <Routes>
        <Route
          path="/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId"
          element={<DesempenoPorComisionDetalleEstudiante />}
        />
        <Route
          path="/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evaluaciones/:evaluacionId/revision"
          element={<p>Revisión completa (docente)</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("DesempenoPorComisionDetalleEstudiante", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el resumen y el detalle del estudiante", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno([evaluacionDetalle("a1", "2026-08-30T10:00:00Z", 14, 3)], {
            total_correctas: 14,
            total_incorrectas: 3,
            porcentaje_acierto: 82,
            cantidad_evaluaciones: 1,
          }),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, [actividadResumen("a1", MATERIA_ID, "Parcial 1")]))

    renderPantalla()

    expect(await screen.findByText("Parcial 1")).toBeInTheDocument()
    expect(screen.getByText("82%")).toBeInTheDocument()

    const [url] = vi.mocked(fetch).mock.calls[0]
    expect(String(url)).toContain(
      `/analytics/materias/${MATERIA_ID}/estudiantes/${ESTUDIANTE_ID}/desempeno`,
    )
  })

  it("estudiante sin evaluaciones finalizadas: muestra el estado vacío", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno([], {
            total_correctas: 0,
            total_incorrectas: 0,
            porcentaje_acierto: 0,
            cantidad_evaluaciones: 0,
          }),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderPantalla()

    expect(
      await screen.findByText(
        "Este estudiante todavía no finalizó ninguna evaluación de esta materia.",
      ),
    ).toBeInTheDocument()
  })

  it("click en una evaluación navega al drill-down 2° (revisión)", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          desempeno([evaluacionDetalle("a1", "2026-08-30T10:00:00Z", 14, 3)], {
            total_correctas: 14,
            total_incorrectas: 3,
            porcentaje_acierto: 82,
            cantidad_evaluaciones: 1,
          }),
        ),
      )
      .mockResolvedValueOnce(jsonResponse(200, [actividadResumen("a1", MATERIA_ID, "Parcial 1")]))

    renderPantalla()
    await screen.findByText("Parcial 1")

    await user.click(screen.getByRole("button", { name: /Parcial 1/ }))

    expect(await screen.findByText("Revisión completa (docente)")).toBeInTheDocument()
  })
})
