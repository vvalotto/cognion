import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SalaEsperaEstudiante } from "./SalaEsperaEstudiante"

afterEach(cleanup)

describe("SalaEsperaEstudiante", () => {
  it("confirma la unión, pide mirar la proyección y muestra el conteo", () => {
    render(<SalaEsperaEstudiante totalParticipantes={14} />)

    expect(screen.getByRole("heading", { name: "¡Te uniste!" })).toBeInTheDocument()
    expect(screen.getByText(/mirá la proyección del aula/)).toBeInTheDocument()
    expect(screen.getByText("14 participantes")).toBeInTheDocument()
    expect(screen.getByRole("status")).toHaveTextContent("Esperando al docente…")
  })

  it("sin botón: la transición es automática", () => {
    render(<SalaEsperaEstudiante totalParticipantes={2} />)
    expect(screen.queryByRole("button")).not.toBeInTheDocument()
  })

  it("en singular con un solo participante", () => {
    render(<SalaEsperaEstudiante totalParticipantes={1} />)
    expect(screen.getByText("1 participante")).toBeInTheDocument()
  })
})
