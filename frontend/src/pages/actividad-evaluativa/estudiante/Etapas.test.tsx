import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EsperaOpciones } from "./EsperaOpciones"
import { PreguntaActiva } from "./PreguntaActiva"
import { ResultadoFinal } from "./ResultadoFinal"
import { ResultadoPregunta } from "./ResultadoPregunta"
import { SinRespuesta } from "./SinRespuesta"
import { vistaEstudiante } from "./_vista-test"

afterEach(cleanup)

const ranking = [1, 2, 3, 4, 5, 6].map((posicion) => ({
  posicion,
  estudianteId: `e${posicion}`,
  nombre: `Estudiante ${posicion}`,
  puntajeAcumulado: 7000 - posicion * 1000,
}))

describe("EsperaOpciones", () => {
  it("muestra 'Pregunta N de total', el enunciado y el mensaje de espera, sin tarjetas", () => {
    render(<EsperaOpciones vista={vistaEstudiante({ etapa: "espera-opciones", opciones: null })} />)
    expect(screen.getByText("Pregunta 3 de 10")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: /depender de una clase concreta/ })).toBeInTheDocument()
    expect(screen.getByRole("status")).toHaveTextContent("Esperá a que el Docente muestre las opciones.")
    expect(screen.queryByRole("button")).not.toBeInTheDocument()
  })
})

describe("PreguntaActiva", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval", "Date"] })
    vi.setSystemTime(new Date("2026-09-25T10:00:00Z"))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("cuatro tarjetas de color con el texto completo, temporizador y el hint del único intento", () => {
    render(<PreguntaActiva vista={vistaEstudiante()} enviando={false} onResponder={() => {}} />)
    const tarjetas = screen.getAllByRole("button")
    expect(tarjetas.map((t) => t.getAttribute("data-color"))).toEqual(["a", "b", "c", "d"])
    expect(tarjetas[1]).toHaveTextContent("Inversión de dependencias")
    expect(tarjetas[0].className).toContain("min-h-[110px]")
    expect(screen.getByRole("timer")).toHaveTextContent("00:20")
    expect(screen.getByText(/un solo intento, no se puede cambiar después/)).toBeInTheDocument()
  })

  it("el temporizador descuenta", () => {
    render(<PreguntaActiva vista={vistaEstudiante()} enviando={false} onResponder={() => {}} />)
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    expect(screen.getByRole("timer")).toHaveTextContent("00:15")
  })

  it("tocar una tarjeta responde al instante con el índice, sin confirmación", () => {
    const onResponder = vi.fn()
    render(<PreguntaActiva vista={vistaEstudiante()} enviando={false} onResponder={onResponder} />)
    fireEvent.click(screen.getByRole("button", { name: "Segregación" }))
    expect(onResponder).toHaveBeenCalledWith({ opcion_indice: 2 })
  })

  it("mientras envía, todas las tarjetas quedan deshabilitadas", () => {
    render(<PreguntaActiva vista={vistaEstudiante()} enviando onResponder={() => {}} />)
    screen.getAllByRole("button").forEach((t) => expect(t).toBeDisabled())
  })

  it("Verdadero/Falso: dos tarjetas que responden con el valor booleano", () => {
    const onResponder = vi.fn()
    render(
      <PreguntaActiva
        vista={vistaEstudiante({ tipo: "verdadero_falso", opciones: null })}
        enviando={false}
        onResponder={onResponder}
      />,
    )
    expect(screen.getAllByRole("button").map((t) => t.textContent)).toEqual(["Verdadero", "Falso"])
    fireEvent.click(screen.getByRole("button", { name: "Falso" }))
    expect(onResponder).toHaveBeenCalledWith({ valor: false })
  })

  it("tres opciones: la tercera ocupa el ancho completo", () => {
    render(
      <PreguntaActiva vista={vistaEstudiante({ opciones: ["x", "y", "z"] })} enviando={false} onResponder={() => {}} />,
    )
    const tarjetas = screen.getAllByRole("button")
    expect(tarjetas).toHaveLength(3)
    expect(tarjetas[2].className).toContain("col-span-2")
    expect(tarjetas[0].className).not.toContain("col-span-2")
  })
})

describe("ResultadoPregunta", () => {
  it("correcta: '¡Correcto!', los puntos de la pregunta y el acumulado, sin ranking ni posición", () => {
    render(
      <ResultadoPregunta
        vista={vistaEstudiante({ etapa: "resultado", resultado: { esCorrecta: true, puntaje: 1850 } })}
      />,
    )
    expect(screen.getByRole("heading", { name: "¡Correcto!" })).toBeInTheDocument()
    expect(screen.getByText("+ 1850 puntos en esta pregunta")).toBeInTheDocument()
    expect(screen.getByText("7420 pts")).toBeInTheDocument()
    expect(screen.queryByText(/°/)).not.toBeInTheDocument()
    expect(screen.queryByRole("list")).not.toBeInTheDocument()
  })

  it("incorrecta: 'Incorrecto' y +0", () => {
    render(
      <ResultadoPregunta vista={vistaEstudiante({ etapa: "resultado", resultado: { esCorrecta: false, puntaje: 0 } })} />,
    )
    expect(screen.getByRole("heading", { name: "Incorrecto" })).toBeInTheDocument()
    expect(screen.getByText("+ 0 puntos en esta pregunta")).toBeInTheDocument()
  })

  it("sin el acierto conocido (tras recargar) muestra solo el acumulado", () => {
    render(<ResultadoPregunta vista={vistaEstudiante({ etapa: "resultado", resultado: null })} />)
    expect(screen.getByRole("heading", { name: "Ya respondiste" })).toBeInTheDocument()
    expect(screen.queryByText(/puntos en esta pregunta/)).not.toBeInTheDocument()
    expect(screen.getByText("7420 pts")).toBeInTheDocument()
  })
})

describe("SinRespuesta", () => {
  it("pregunta cerrada: 'No respondiste (+0)' con el acumulado", () => {
    render(<SinRespuesta vista={vistaEstudiante({ etapa: "sin-respuesta", motivoSinRespuesta: "cierre" })} />)
    expect(screen.getByRole("heading", { name: "Se cerró la pregunta" })).toBeInTheDocument()
    expect(screen.getByText("No respondiste (+0)")).toBeInTheDocument()
    expect(screen.getByText("7420 pts")).toBeInTheDocument()
  })

  it("tiempo agotado: 'Se acabó el tiempo' con el acumulado", () => {
    render(<SinRespuesta vista={vistaEstudiante({ etapa: "sin-respuesta", motivoSinRespuesta: "tiempo" })} />)
    expect(screen.getByRole("heading", { name: "Se acabó el tiempo" })).toBeInTheDocument()
    expect(screen.getByText("Se acabó el tiempo antes de tu respuesta (+0)")).toBeInTheDocument()
  })
})

describe("ResultadoFinal", () => {
  it("en el Top 3: posición destacada y su fila resaltada", () => {
    render(<ResultadoFinal ranking={ranking} estudianteId="e2" />)
    expect(screen.getByText("Quedaste 2° con 5000 puntos")).toBeInTheDocument()
    const filas = within(screen.getByRole("list", { name: "Ranking final" })).getAllByRole("listitem")
    expect(filas).toHaveLength(3)
    expect(filas[1]).toHaveAttribute("data-propia", "true")
    expect(filas[1]).toHaveTextContent("Vos")
    expect(filas[0]).toHaveTextContent("Estudiante 1")
  })

  it("fuera del Top 3: el Top 3 y su propia fila debajo con su posición", () => {
    render(<ResultadoFinal ranking={ranking} estudianteId="e5" />)
    expect(screen.getByText("Quedaste 5° con 2000 puntos")).toBeInTheDocument()
    const filas = within(screen.getByRole("list", { name: "Ranking final" })).getAllByRole("listitem")
    expect(filas).toHaveLength(4)
    expect(filas[3]).toHaveAttribute("data-propia", "true")
    expect(filas[3]).toHaveTextContent("5")
  })

  it("si no figura en el ranking", () => {
    render(<ResultadoFinal ranking={ranking.slice(0, 2)} estudianteId="otro" />)
    expect(screen.getByText("No sumaste puntos en esta sesión")).toBeInTheDocument()
  })

  it("sin ranking no dibuja la lista", () => {
    render(<ResultadoFinal ranking={[]} estudianteId="e1" />)
    expect(screen.queryByRole("list")).not.toBeInTheDocument()
  })
})
