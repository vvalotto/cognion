import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { HomeDocente } from "@/pages/HomeDocente"

function renderHomeDocente() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<HomeDocente />} />
        <Route path="/materias" element={<p>Materias</p>} />
        <Route path="/actividad-evaluativa/materias" element={<p>Mis materias</p>} />
        <Route path="/analytics/desempeno-por-alumno" element={<p>Desempeño por alumno</p>} />
        <Route path="/analytics/desempeno-por-tema" element={<p>Desempeño por tema</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("HomeDocente", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el saludo genérico", () => {
    renderHomeDocente()

    expect(screen.getByRole("heading", { name: "Hola, Docente" })).toBeInTheDocument()
  })

  it("muestra las 4 cards de acceso", () => {
    renderHomeDocente()

    expect(screen.getByText("Banco de Preguntas")).toBeInTheDocument()
    expect(screen.getByText("Actividades")).toBeInTheDocument()
    expect(screen.getByText("Desempeño por alumno")).toBeInTheDocument()
    expect(screen.getByText("Desempeño por tema")).toBeInTheDocument()
  })

  it("navega a /materias al hacer clic en Banco de Preguntas", async () => {
    renderHomeDocente()
    const user = userEvent.setup()

    await user.click(screen.getByText("Banco de Preguntas"))

    expect(await screen.findByText("Materias")).toBeInTheDocument()
  })

  it("navega a /actividad-evaluativa/materias al hacer clic en Actividades", async () => {
    renderHomeDocente()
    const user = userEvent.setup()

    await user.click(screen.getByText("Actividades"))

    expect(await screen.findByText("Mis materias")).toBeInTheDocument()
  })

  it("navega con Enter cuando la card tiene foco", async () => {
    renderHomeDocente()
    const user = userEvent.setup()

    ;(screen.getByText("Desempeño por alumno").closest('[role="button"]') as HTMLElement).focus()
    await user.keyboard("{Enter}")

    await waitFor(() => {
      expect(screen.queryByText("Banco de Preguntas")).not.toBeInTheDocument()
    })
  })
})
