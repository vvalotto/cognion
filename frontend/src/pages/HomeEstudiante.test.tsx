import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { HomeEstudiante } from "@/pages/HomeEstudiante"

function renderHomeEstudiante() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<HomeEstudiante />} />
        <Route path="/mis-actividades/materias" element={<p>Mis materias</p>} />
        <Route path="/analytics/mi-desempeno" element={<p>Mi desempeño</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("HomeEstudiante", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el saludo genérico", () => {
    renderHomeEstudiante()

    expect(screen.getByRole("heading", { name: "Hola, Estudiante" })).toBeInTheDocument()
  })

  it("muestra las 2 cards de acceso", () => {
    renderHomeEstudiante()

    expect(screen.getByText("Mis Actividades")).toBeInTheDocument()
    expect(screen.getByText("Mi Desempeño")).toBeInTheDocument()
  })

  it("navega a /mis-actividades/materias al hacer clic en Mis Actividades", async () => {
    renderHomeEstudiante()
    const user = userEvent.setup()

    await user.click(screen.getByText("Mis Actividades"))

    expect(await screen.findByText("Mis materias")).toBeInTheDocument()
  })

  it("navega a /analytics/mi-desempeno al hacer clic en Mi Desempeño", async () => {
    renderHomeEstudiante()
    const user = userEvent.setup()

    await user.click(screen.getByText("Mi Desempeño"))

    expect(await screen.findByText("Mi desempeño")).toBeInTheDocument()
  })

  it("navega con Enter cuando la card tiene foco", async () => {
    renderHomeEstudiante()
    const user = userEvent.setup()

    ;(screen.getByText("Mis Actividades").closest('[role="button"]') as HTMLElement).focus()
    await user.keyboard("{Enter}")

    await waitFor(() => {
      expect(screen.queryByText("Mi Desempeño")).not.toBeInTheDocument()
    })
  })
})
