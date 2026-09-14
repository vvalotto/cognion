import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

import { DesempenoResumenDetalle, type FilaDesempeno } from "@/pages/analytics/DesempenoResumenDetalle"
import type { DesempenoEstudianteResponse } from "@/lib/analytics-api"

const DESEMPENO: DesempenoEstudianteResponse = {
  evaluaciones: [],
  resumen: {
    totalCorrectas: 14,
    totalIncorrectas: 3,
    porcentajeAcierto: 82,
    cantidadEvaluaciones: 1,
  },
}

const FILAS: FilaDesempeno[] = [
  {
    evaluacionId: "e1",
    titulo: "Parcial 1",
    finalizadaEn: "2026-08-30T10:00:00Z",
    cantidadCorrectas: 14,
    cantidadIncorrectas: 3,
  },
]

describe("DesempenoResumenDetalle", () => {
  afterEach(() => cleanup())

  it("sin onFilaClick: la fila no es clicable", () => {
    render(
      <DesempenoResumenDetalle desempeno={DESEMPENO} filas={FILAS} mensajeVacio="Vacío" />,
    )

    expect(screen.getByText("Parcial 1")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /Parcial 1/ })).not.toBeInTheDocument()
  })

  it("con onFilaClick: click en una .eval-item invoca el callback con el evaluacionId", async () => {
    const user = userEvent.setup()
    const onFilaClick = vi.fn()
    render(
      <DesempenoResumenDetalle
        desempeno={DESEMPENO}
        filas={FILAS}
        mensajeVacio="Vacío"
        onFilaClick={onFilaClick}
      />,
    )

    await user.click(screen.getByRole("button", { name: /Parcial 1/ }))

    expect(onFilaClick).toHaveBeenCalledWith("e1")
  })

  it("con onFilaClick: la tecla Enter también invoca el callback", async () => {
    const user = userEvent.setup()
    const onFilaClick = vi.fn()
    render(
      <DesempenoResumenDetalle
        desempeno={DESEMPENO}
        filas={FILAS}
        mensajeVacio="Vacío"
        onFilaClick={onFilaClick}
      />,
    )

    const fila = screen.getByRole("button", { name: /Parcial 1/ })
    fila.focus()
    await user.keyboard("{Enter}")

    expect(onFilaClick).toHaveBeenCalledWith("e1")
  })

  it("con onFilaClick: la tecla espacio también invoca el callback", async () => {
    const user = userEvent.setup()
    const onFilaClick = vi.fn()
    render(
      <DesempenoResumenDetalle
        desempeno={DESEMPENO}
        filas={FILAS}
        mensajeVacio="Vacío"
        onFilaClick={onFilaClick}
      />,
    )

    const fila = screen.getByRole("button", { name: /Parcial 1/ })
    fila.focus()
    await user.keyboard(" ")

    expect(onFilaClick).toHaveBeenCalledWith("e1")
  })

  it("con onFilaClick: una tecla que no es Enter ni espacio no invoca el callback", async () => {
    const user = userEvent.setup()
    const onFilaClick = vi.fn()
    render(
      <DesempenoResumenDetalle
        desempeno={DESEMPENO}
        filas={FILAS}
        mensajeVacio="Vacío"
        onFilaClick={onFilaClick}
      />,
    )

    const fila = screen.getByRole("button", { name: /Parcial 1/ })
    fila.focus()
    await user.keyboard("a")

    expect(onFilaClick).not.toHaveBeenCalled()
  })

  it("sin filas: muestra el mensaje vacío en vez de la tabla", () => {
    render(
      <DesempenoResumenDetalle
        desempeno={DESEMPENO}
        filas={[]}
        mensajeVacio="Todavía no hay evaluaciones."
      />,
    )

    expect(screen.getByText("Todavía no hay evaluaciones.")).toBeInTheDocument()
  })
})
