import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EditarPregunta } from "@/pages/EditarPregunta"

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

const preguntaOpcionMultiple = {
  id: "p1",
  banco_id: "b1",
  texto: "¿Qué principio de Clean Architecture prohíbe importar una capa externa?",
  opciones: [
    { texto: "DIP", es_correcta: true },
    { texto: "SRP", es_correcta: false },
  ],
  unidad_tematica: "Unidad 3",
  tema: "Arquitectura",
  dificultad: "alto",
  importancia: "alto",
  activa: true,
}

const preguntaVerdaderoFalso = {
  id: "p2",
  banco_id: "b1",
  texto: "Un Aggregate Root solo referencia a otro por identidad.",
  respuesta_correcta: true,
  unidad_tematica: "Unidad 2",
  tema: "DDD",
  dificultad: "medio",
  importancia: "alto",
  activa: true,
}

const preguntasResponse = [preguntaOpcionMultiple, preguntaVerdaderoFalso]

function renderEdicion(preguntaId: string) {
  return render(
    <MemoryRouter initialEntries={[`/materias/m1/banco/preguntas/${preguntaId}/editar`]}>
      <Routes>
        <Route
          path="/materias/:materiaId/banco/preguntas/:preguntaId/editar"
          element={<EditarPregunta />}
        />
        <Route path="/materias/:materiaId/banco" element={<p>Banco</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EditarPregunta", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("prellena el formulario de Opción Múltiple con los valores actuales", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderEdicion("p1")

    expect(await screen.findByDisplayValue(preguntaOpcionMultiple.texto)).toBeInTheDocument()
    expect(screen.getByDisplayValue("DIP")).toBeInTheDocument()
    expect(screen.getByDisplayValue("SRP")).toBeInTheDocument()
    expect(screen.getByLabelText("Marcar opción 1 como correcta")).toBeChecked()
    expect(screen.getByDisplayValue("Unidad 3")).toBeInTheDocument()
    expect(screen.queryByText(/Elegir tipo/)).not.toBeInTheDocument()
  })

  it("edición exitosa de Opción Múltiple persiste los cambios y vuelve al banco", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, { ...preguntaOpcionMultiple, texto: "Texto editado" }))
    const user = userEvent.setup()

    renderEdicion("p1")
    const textoInput = await screen.findByDisplayValue(preguntaOpcionMultiple.texto)
    await user.clear(textoInput)
    await user.type(textoInput, "Texto editado")

    await user.click(screen.getByText("Guardar cambios"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(ultimaLlamada?.[0]).toContain("/preguntas/p1")
    expect((ultimaLlamada![1] as RequestInit).method).toBe("PUT")
    const body = JSON.parse((ultimaLlamada![1] as RequestInit).body as string)
    expect(body.texto).toBe("Texto editado")
  })

  it("rechazo de cliente por opciones inválidas bloquea el envío sin llamar al backend", async () => {
    const preguntaSinCorrecta = {
      ...preguntaOpcionMultiple,
      opciones: preguntaOpcionMultiple.opciones.map((o) => ({ ...o, es_correcta: false })),
    }
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado([preguntaSinCorrecta, preguntaVerdaderoFalso])))
    const user = userEvent.setup()

    renderEdicion("p1")
    await screen.findByDisplayValue(preguntaOpcionMultiple.texto)

    await user.click(screen.getByText("Guardar cambios"))

    expect(
      await screen.findByText("Marcá exactamente una opción como correcta."),
    ).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it("prellena el formulario de Verdadero/Falso con la respuesta actual", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderEdicion("p2")

    expect(await screen.findByDisplayValue(preguntaVerdaderoFalso.texto)).toBeInTheDocument()
    expect(screen.getByText("Verdadero")).toHaveAttribute("aria-pressed", "true")
    expect(screen.getByText("Falso")).toHaveAttribute("aria-pressed", "false")
  })

  it("pregunta inexistente muestra un mensaje en vez del formulario", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderEdicion("no-existe")

    expect(
      await screen.findByText("No se encontró la pregunta a editar."),
    ).toBeInTheDocument()
  })

  it("edición exitosa de Verdadero/Falso persiste los cambios y vuelve al banco", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(
        jsonResponse(200, { ...preguntaVerdaderoFalso, respuesta_correcta: false }),
      )
    const user = userEvent.setup()

    renderEdicion("p2")
    await screen.findByDisplayValue(preguntaVerdaderoFalso.texto)

    await user.click(screen.getByText("Falso"))
    await user.selectOptions(screen.getByLabelText("Dificultad"), "bajo")
    await user.selectOptions(screen.getByLabelText("Importancia"), "bajo")

    await user.click(screen.getByText("Guardar cambios"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    const body = JSON.parse((ultimaLlamada![1] as RequestInit).body as string)
    expect(body.respuesta_correcta).toBe(false)
    expect(body.dificultad).toBe("bajo")
    expect(body.importancia).toBe("bajo")
  })

  it("editar el texto de una opción y agregar/quitar opciones en Opción Múltiple", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, preguntaOpcionMultiple))
    const user = userEvent.setup()

    renderEdicion("p1")
    await screen.findByDisplayValue(preguntaOpcionMultiple.texto)

    await user.click(screen.getByText("+ Agregar opción"))
    const opciones = screen.getAllByPlaceholderText(/Opción \d/)
    await user.type(opciones[2], "LSP")
    await user.click(screen.getByLabelText("Marcar opción 3 como correcta"))

    const dipInput = screen.getByDisplayValue("DIP")
    await user.clear(dipInput)
    await user.type(dipInput, "DIP editado")

    await user.click(screen.getByLabelText("Quitar opción 2"))
    await user.click(screen.getByText("Guardar cambios"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    const body = JSON.parse((ultimaLlamada![1] as RequestInit).body as string)
    expect(body.opciones).toHaveLength(2)
    expect(body.opciones.map((o: { texto: string }) => o.texto)).toEqual([
      "DIP editado",
      "LSP",
    ])
  })

  it("sugiere las unidades y temas de las demás preguntas del banco (US-ADJ-02)", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))

    renderEdicion("p1")
    await screen.findByDisplayValue(preguntaOpcionMultiple.texto)

    await waitFor(() => {
      const valores = Array.from(
        document.getElementById("editar-unidad-sugerencias")?.querySelectorAll("option") ?? [],
      ).map((o) => o.getAttribute("value"))
      expect(valores).toEqual(["Unidad 2", "Unidad 3"])
    })
  })

  it("'Cancelar' vuelve al banco sin llamar al backend", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(200, paginado(preguntasResponse)))
    const user = userEvent.setup()

    renderEdicion("p1")
    await screen.findByDisplayValue(preguntaOpcionMultiple.texto)

    await user.click(screen.getByText("Cancelar"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})
