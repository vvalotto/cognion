import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { StagePreguntaOpciones } from "@/pages/actividad-evaluativa/proyeccion/StagePreguntaOpciones"
import type { VistaProyeccion } from "@/pages/actividad-evaluativa/proyeccion/vista-proyeccion"

const ahora = new Date("2026-09-23T10:00:00Z").getTime()

const vista: VistaProyeccion = {
  etapa: "pregunta-opciones",
  indice: 2,
  cantidadPreguntas: 10,
  enunciado: "¿Qué es SOLID?",
  tipo: "opcion_multiple",
  opciones: ["Liskov", "Inversión de dependencias", "Segregación", "Responsabilidad única"],
  tiempoLimiteSegundos: 20,
  inicioOpcionesMs: ahora,
  cantidadRespuestas: 3,
  totalParticipantes: 5,
  resultado: null,
}

describe("StagePreguntaOpciones", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(ahora)
  })

  afterEach(() => {
    vi.useRealTimers()
    cleanup()
  })

  it("muestra las 4 opciones como cajas de color, sin marcar ninguna como correcta", () => {
    render(<StagePreguntaOpciones vista={vista} enviando={false} onCerrarPregunta={() => {}} />)

    const cajas = screen.getAllByRole("listitem")
    expect(cajas.map((c) => c.getAttribute("data-color"))).toEqual(["a", "b", "c", "d"])
    expect(cajas[1]).toHaveTextContent("Inversión de dependencias")
    cajas.forEach((c) => {
      expect(c.querySelector("svg, img")).toBeNull()
      expect(c).not.toHaveAttribute("aria-current")
      expect(c.className).not.toContain("correcta")
    })
    expect(screen.getByText("Pregunta 3 de 10")).toBeInTheDocument()
  })

  it("Verdadero/Falso muestra dos cajas", () => {
    render(
      <StagePreguntaOpciones
        vista={{ ...vista, tipo: "verdadero_falso", opciones: null }}
        enviando={false}
        onCerrarPregunta={() => {}}
      />,
    )
    expect(screen.getAllByRole("listitem").map((c) => c.textContent)).toEqual(["Verdadero", "Falso"])
  })

  it("con 3 opciones la tercera ocupa el ancho completo", () => {
    render(
      <StagePreguntaOpciones
        vista={{ ...vista, opciones: ["x", "y", "z"] }}
        enviando={false}
        onCerrarPregunta={() => {}}
      />,
    )
    const cajas = screen.getAllByRole("listitem")
    expect(cajas).toHaveLength(3)
    expect(cajas[2].className).toContain("col-span-2")
    expect(cajas[0].className).not.toContain("col-span-2")
  })

  it("el temporizador cuenta desde el tiempo límite y la barra baja", () => {
    render(<StagePreguntaOpciones vista={vista} enviando={false} onCerrarPregunta={() => {}} />)
    expect(screen.getByRole("timer")).toHaveTextContent("00:20")
    expect(screen.getByTestId("barra-progreso")).toHaveStyle({ width: "100%" })

    act(() => {
      vi.advanceTimersByTime(10_000)
    })
    expect(screen.getByRole("timer")).toHaveTextContent("00:10")
    expect(screen.getByTestId("barra-progreso")).toHaveStyle({ width: "50%" })
  })

  it("con la apertura hace 10 segundos descuenta esos segundos", () => {
    render(
      <StagePreguntaOpciones
        vista={{ ...vista, inicioOpcionesMs: ahora - 10_000 }}
        enviando={false}
        onCerrarPregunta={() => {}}
      />,
    )
    expect(screen.getByRole("timer")).toHaveTextContent("00:10")
  })

  it("el temporizador en 0 no cierra la pregunta: el botón sigue disponible", () => {
    const onCerrar = vi.fn()
    render(<StagePreguntaOpciones vista={vista} enviando={false} onCerrarPregunta={onCerrar} />)

    act(() => {
      vi.advanceTimersByTime(60_000)
    })
    expect(screen.getByRole("timer")).toHaveTextContent("00:00")
    expect(onCerrar).not.toHaveBeenCalled()
    expect(screen.getByRole("button", { name: "Cerrar pregunta" })).toBeEnabled()
  })

  it("muestra solo el total del conteo, sin desglose por opción", () => {
    render(<StagePreguntaOpciones vista={vista} enviando={false} onCerrarPregunta={() => {}} />)
    expect(screen.getByText(/ya respondieron/)).toHaveTextContent("3 / 5 ya respondieron")
  })

  it("'Cerrar pregunta' avisa al contenedor y se deshabilita mientras envía", () => {
    const onCerrar = vi.fn()
    const { rerender } = render(
      <StagePreguntaOpciones vista={vista} enviando={false} onCerrarPregunta={onCerrar} />,
    )
    fireEvent.click(screen.getByRole("button", { name: "Cerrar pregunta" }))
    expect(onCerrar).toHaveBeenCalledTimes(1)

    rerender(<StagePreguntaOpciones vista={vista} enviando onCerrarPregunta={onCerrar} />)
    expect(screen.getByRole("button", { name: "Cerrar pregunta" })).toBeDisabled()
  })
})
