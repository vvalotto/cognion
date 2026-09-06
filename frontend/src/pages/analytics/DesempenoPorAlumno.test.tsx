import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { DesempenoPorAlumno } from "@/pages/analytics/DesempenoPorAlumno"

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

function estudiante(id: string, nombre: string) {
  return { id, nombre }
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

function desempeno(evaluaciones: unknown[], resumen: Record<string, number>) {
  return { evaluaciones, resumen }
}

function evaluacionDetalle(actividadId: string, finalizadaEn: string, correctas: number, incorrectas: number) {
  return {
    evaluacion_id: `ev-${actividadId}`,
    actividad_id: actividadId,
    finalizada_en: finalizadaEn,
    cantidad_correctas: correctas,
    cantidad_incorrectas: incorrectas,
  }
}

function renderPantalla() {
  return render(
    <MemoryRouter>
      <DesempenoPorAlumno />
    </MemoryRouter>,
  )
}

describe("DesempenoPorAlumno", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("estado inicial: placeholder sin resumen ni lista", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )

    renderPantalla()

    expect(
      await screen.findByText("Elegí un estudiante para ver su desempeño."),
    ).toBeInTheDocument()
  })

  it("recorrido completo en cascada: Materia → Comisión → Estudiante muestra resumen y detalle", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí un estudiante para ver su desempeño.")

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [comision("c1", "Lunes 18-20hs")]),
    )
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [estudiante("u1", "Ana Pérez")]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await waitFor(() => expect(screen.getByLabelText("Estudiante")).not.toBeDisabled())

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
      .mockResolvedValueOnce(jsonResponse(200, [actividadResumen("a1", "m1", "Parcial 1")]))

    await user.selectOptions(screen.getByLabelText("Estudiante"), "u1")

    expect(await screen.findByText("Parcial 1")).toBeInTheDocument()
    expect(screen.getByText("14")).toBeInTheDocument()
    expect(screen.getByText("82%")).toBeInTheDocument()

    const [url] = vi.mocked(fetch).mock.calls.at(-2) ?? []
    expect(String(url)).toContain("/analytics/materias/m1/estudiantes/u1/desempeno")
  })

  it("estudiante sin evaluaciones finalizadas: muestra el estado vacío", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí un estudiante para ver su desempeño.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [estudiante("u2", "Juan Gómez")]))
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await waitFor(() => expect(screen.getByLabelText("Estudiante")).not.toBeDisabled())

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

    await user.selectOptions(screen.getByLabelText("Estudiante"), "u2")

    expect(
      await screen.findByText(
        "Este estudiante todavía no finalizó ninguna evaluación de esta materia.",
      ),
    ).toBeInTheDocument()
  })

  it("cambiar de Materia reinicia Comisión, Estudiante y el resultado mostrado", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software"), materia("m2", "Gestión de Proyectos")]),
    )
    renderPantalla()
    await screen.findByText("Elegí un estudiante para ver su desempeño.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [estudiante("u1", "Ana Pérez")]))
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await waitFor(() => expect(screen.getByLabelText("Estudiante")).not.toBeDisabled())

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
      .mockResolvedValueOnce(jsonResponse(200, [actividadResumen("a1", "m1", "Parcial 1")]))
    await user.selectOptions(screen.getByLabelText("Estudiante"), "u1")
    expect(await screen.findByText("Parcial 1")).toBeInTheDocument()

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c2", "Martes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m2")

    expect(
      await screen.findByText("Elegí un estudiante para ver su desempeño."),
    ).toBeInTheDocument()
    expect(screen.queryByText("Parcial 1")).not.toBeInTheDocument()
    expect(screen.getByLabelText("Comisión")).toHaveValue("")
    expect(screen.getByLabelText("Estudiante")).toBeDisabled()
  })
})
