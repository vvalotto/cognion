import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { DesempenoPorComision } from "@/pages/analytics/DesempenoPorComision"

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

function filaComision(
  estudianteId: string,
  nombre: string,
  porcentaje: number | null,
  pendientes: number,
) {
  return {
    estudiante_id: estudianteId,
    nombre,
    porcentaje_aciertos_acumulado: porcentaje,
    actividades_pendientes: pendientes,
  }
}

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/analytics/desempeno-por-comision"]}>
      <Routes>
        <Route path="/analytics/desempeno-por-comision" element={<DesempenoPorComision />} />
        <Route
          path="/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId"
          element={<p>Detalle del estudiante</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("DesempenoPorComision", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("estado inicial: placeholder sin tabla", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )

    renderPantalla()

    expect(
      await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes."),
    ).toBeInTheDocument()
  })

  it("Materia → Comisión muestra la tabla con estados mixtos ('Sin datos' y pendientes en ámbar)", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        filaComision("u1", "Ana Pérez", 82, 0),
        filaComision("u2", "Juan Gómez", null, 2),
      ]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")

    expect(await screen.findByText("Ana Pérez")).toBeInTheDocument()
    expect(screen.getByText("82%")).toBeInTheDocument()
    expect(screen.getByText("Sin datos")).toBeInTheDocument()
    expect(screen.getByText("2")).toBeInTheDocument()

    const [url] = vi.mocked(fetch).mock.calls.at(-1) ?? []
    expect(String(url)).toContain("/analytics/materias/m1/comisiones/c1/desempeno")
  })

  it("comisión sin evaluaciones finalizadas: todas las filas en 'Sin datos'", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [filaComision("u1", "Ana Pérez", null, 0)]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")

    expect(await screen.findByText("Sin datos")).toBeInTheDocument()
  })

  it("click en una fila navega al drill-down 1° (detalle del estudiante)", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [filaComision("u1", "Ana Pérez", 82, 0)]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await screen.findByText("Ana Pérez")

    await user.click(screen.getByText("Ana Pérez"))

    expect(await screen.findByText("Detalle del estudiante")).toBeInTheDocument()
  })

  it("ordena la tabla por columna al hacer click en el encabezado", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        filaComision("u1", "Zulema Ríos", 60, 0),
        filaComision("u2", "Ana Pérez", 90, 0),
      ]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await screen.findByText("Zulema Ríos")

    const filasAntes = screen.getAllByRole("row").slice(1)
    expect(filasAntes[0]).toHaveTextContent("Ana Pérez")

    await user.click(screen.getByText("Nombre"))

    const filasDespues = screen.getAllByRole("row").slice(1)
    expect(filasDespues[0]).toHaveTextContent("Zulema Ríos")
  })

  it("ordena por % Aciertos ascendente, tratando 'Sin datos' como el valor más bajo", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        filaComision("u1", "Ana Pérez", 90, 0),
        filaComision("u2", "Juan Gómez", null, 0),
        filaComision("u3", "Luis Díaz", 60, 0),
      ]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await screen.findByText("Ana Pérez")

    await user.click(screen.getByText("% Aciertos"))

    const filas = screen.getAllByRole("row").slice(1)
    expect(filas[0]).toHaveTextContent("Juan Gómez")
    expect(filas[1]).toHaveTextContent("Luis Díaz")
    expect(filas[2]).toHaveTextContent("Ana Pérez")
  })

  it("click en el encabezado ya activo invierte la dirección del orden (por defecto asc por Nombre)", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        filaComision("u1", "Ana Pérez", 90, 0),
        filaComision("u2", "Zulema Ríos", 60, 0),
      ]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    await screen.findByText("Ana Pérez")

    await user.click(screen.getByText("Nombre"))

    const filas = screen.getAllByRole("row").slice(1)
    expect(filas[0]).toHaveTextContent("Zulema Ríos")
  })

  it("la tecla Enter en una fila navega al drill-down 1° igual que el click", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [filaComision("u1", "Ana Pérez", 82, 0)]),
    )
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")
    const fila = await screen.findByText("Ana Pérez")

    fila.closest("tr")?.focus()
    await user.keyboard("{Enter}")

    expect(await screen.findByText("Detalle del estudiante")).toBeInTheDocument()
  })

  it("error de red al consultar el desempeño: muestra el mensaje de error", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [materia("m1", "Ingeniería de Software")]),
    )
    renderPantalla()
    await screen.findByText("Elegí una comisión para ver el desempeño de sus estudiantes.")

    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [comision("c1", "Lunes 18-20hs")]))
    await user.selectOptions(screen.getByLabelText("Materia"), "m1")
    await waitFor(() => expect(screen.getByLabelText("Comisión")).not.toBeDisabled())

    vi.mocked(fetch).mockRejectedValueOnce(new Error("network error"))
    await user.selectOptions(screen.getByLabelText("Comisión"), "c1")

    expect(
      await screen.findByText(
        "No se pudo cargar el desempeño de la comisión. Intentá de nuevo más tarde.",
      ),
    ).toBeInTheDocument()
  })
})
