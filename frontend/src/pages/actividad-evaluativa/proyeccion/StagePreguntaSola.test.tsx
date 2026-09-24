import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

import { StagePreguntaSola } from "@/pages/actividad-evaluativa/proyeccion/StagePreguntaSola"
import type { VistaProyeccion } from "@/pages/actividad-evaluativa/proyeccion/vista-proyeccion"

const vista: VistaProyeccion = {
  etapa: "pregunta-sola",
  comisionId: "c1",
  indice: 0,
  cantidadPreguntas: 5,
  enunciado: "¿Qué principio viola depender de una clase concreta?",
  tipo: "opcion_multiple",
  opciones: null,
  tiempoLimiteSegundos: 20,
  inicioOpcionesMs: 0,
  cantidadRespuestas: 0,
  totalParticipantes: 3,
  resultado: null,
}

afterEach(cleanup)

describe("StagePreguntaSola", () => {
  it("muestra el enunciado, 'Pregunta 1 de N' y el botón, sin opciones", () => {
    render(<StagePreguntaSola vista={vista} enviando={false} onMostrarOpciones={() => {}} />)

    expect(screen.getByRole("heading", { name: /depender de una clase concreta/ })).toBeInTheDocument()
    expect(screen.getByText("Pregunta 1 de 5")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Mostrar opciones" })).toBeEnabled()
    expect(screen.queryByRole("list")).not.toBeInTheDocument()
    expect(screen.queryByRole("timer")).not.toBeInTheDocument()
  })

  it("el enunciado usa la tipografía de proyección (≥ 40 px)", () => {
    render(<StagePreguntaSola vista={vista} enviando={false} onMostrarOpciones={() => {}} />)
    expect(screen.getByRole("heading").className).toContain("text-[40px]")
  })

  it("pulsar el botón avisa al contenedor", async () => {
    const onMostrar = vi.fn()
    render(<StagePreguntaSola vista={vista} enviando={false} onMostrarOpciones={onMostrar} />)

    await userEvent.click(screen.getByRole("button", { name: "Mostrar opciones" }))
    expect(onMostrar).toHaveBeenCalledTimes(1)
  })

  it("mientras envía el botón queda deshabilitado", () => {
    render(<StagePreguntaSola vista={vista} enviando onMostrarOpciones={() => {}} />)
    expect(screen.getByRole("button", { name: "Mostrar opciones" })).toBeDisabled()
  })
})
