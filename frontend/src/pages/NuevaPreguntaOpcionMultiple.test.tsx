import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { NuevaPreguntaOpcionMultiple } from "@/pages/NuevaPreguntaOpcionMultiple"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function paginado<T>(preguntas: T[]): { preguntas: T[]; total: number } {
  return { preguntas, total: preguntas.length }
}

const materiaResponse = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 2 },
]

const preguntaCreadaResponse = {
  id: "p9",
  banco_id: "b1",
  texto: "¿Cuál es la capa más interna?",
  opciones: [
    { texto: "Entities", es_correcta: true },
    { texto: "Frameworks", es_correcta: false },
  ],
  unidad_tematica: "Unidad 1",
  tema: "Clean Architecture",
  dificultad: "medio",
  importancia: "alto",
  activa: true,
}

function renderFormulario() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/banco/preguntas/nueva/opcion-multiple"]}>
      <Routes>
        <Route
          path="/materias/:materiaId/banco/preguntas/nueva/opcion-multiple"
          element={<NuevaPreguntaOpcionMultiple />}
        />
        <Route path="/materias/:materiaId/banco" element={<p>Banco</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

async function completarCamposComunes(
  user: ReturnType<typeof userEvent.setup>,
  texto: string,
) {
  await user.type(await screen.findByLabelText("Texto de la pregunta"), texto)
  await user.type(screen.getByLabelText("Unidad temática"), "Unidad 1")
  await user.type(screen.getByLabelText("Tema"), "Clean Architecture")
}

describe("NuevaPreguntaOpcionMultiple", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("carga exitosa con 3 opciones y una marcada correcta vuelve al banco", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
      .mockResolvedValueOnce(jsonResponse(201, preguntaCreadaResponse))
    const user = userEvent.setup()

    renderFormulario()
    await completarCamposComunes(user, "¿Cuál es la capa más interna?")

    await user.click(screen.getByText("+ Agregar opción"))
    const opciones = screen.getAllByPlaceholderText(/Opción \d/)
    await user.type(opciones[0], "Entities")
    await user.type(opciones[1], "Frameworks")
    await user.type(opciones[2], "Use Cases")
    await user.click(screen.getByLabelText("Marcar opción 1 como correcta"))

    await user.click(screen.getByText("Guardar pregunta"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    const [, , terceraLlamada] = vi.mocked(fetch).mock.calls
    const [, opciones2] = terceraLlamada
    const body = JSON.parse((opciones2 as RequestInit).body as string)
    expect(body.opciones).toHaveLength(3)
    expect(body.opciones.filter((o: { es_correcta: boolean }) => o.es_correcta)).toHaveLength(1)
  })

  it("sugiere unidades y temas ya usados en el banco (US-ADJ-02)", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([preguntaCreadaResponse])))

    renderFormulario()
    await screen.findByLabelText("Texto de la pregunta")

    await waitFor(() => {
      expect(
        document
          .getElementById("om-unidad-sugerencias")
          ?.querySelector("option")
          ?.getAttribute("value"),
      ).toBe("Unidad 1")
    })
    expect(
      document.getElementById("om-tema-sugerencias")?.querySelector("option")?.getAttribute("value"),
    ).toBe("Clean Architecture")
  })

  it("sin ninguna opción marcada como correcta bloquea el envío y no llama al backend", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
    const user = userEvent.setup()

    renderFormulario()
    await completarCamposComunes(user, "¿Cuál es la capa más interna?")
    const opciones = screen.getAllByPlaceholderText(/Opción \d/)
    await user.type(opciones[0], "Entities")
    await user.type(opciones[1], "Frameworks")

    await user.click(screen.getByText("Guardar pregunta"))

    expect(
      await screen.findByText("Marcá exactamente una opción como correcta."),
    ).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it("quitar una opción no permite bajar de 2", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
    renderFormulario()

    await screen.findByLabelText("Texto de la pregunta")
    const botonesQuitar = screen.getAllByLabelText(/Quitar opción/)
    expect(botonesQuitar[0]).toBeDisabled()
    expect(botonesQuitar[1]).toBeDisabled()
  })
})
