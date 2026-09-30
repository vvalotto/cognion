import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

import {
  armarFilasEnVivo,
  DesempenoResumenDetalle,
  type FilaDesempeno,
  type FilaSesionEnVivo,
} from "@/pages/analytics/DesempenoResumenDetalle"
import type { DesempenoEstudianteResponse, SesionEnVivoDesempenoResponse } from "@/lib/analytics-api"

const DESEMPENO: DesempenoEstudianteResponse = {
  evaluaciones: [],
  resumen: {
    totalCorrectas: 14,
    totalIncorrectas: 3,
    porcentajeAcierto: 82,
    cantidadEvaluaciones: 1,
  },
  sesionesEnVivo: [],
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

function sesionEnVivo(
  sesionId: string,
  finalizadaEn: string,
  overrides: Partial<SesionEnVivoDesempenoResponse> = {},
): SesionEnVivoDesempenoResponse {
  return {
    sesionId,
    comisionHorario: "Lunes 14-16hs",
    finalizadaEn,
    cantidadPreguntas: 5,
    cantidadCorrectas: 3,
    cantidadIncorrectas: 2,
    puntajeFinal: 800,
    posicion: 2,
    totalParticipantes: 14,
    ...overrides,
  }
}

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

  describe("sección Sesiones en vivo (US-ADJ-56)", () => {
    it("sin filasEnVivo/mensajeVacioEnVivo: no se renderiza la sección", () => {
      render(<DesempenoResumenDetalle desempeno={DESEMPENO} filas={FILAS} mensajeVacio="Vacío" />)

      expect(screen.queryByText("Sesiones en vivo")).not.toBeInTheDocument()
    })

    it("filasEnVivo vacío: muestra el mensaje vacío de sesiones en vivo", () => {
      render(
        <DesempenoResumenDetalle
          desempeno={DESEMPENO}
          filas={FILAS}
          mensajeVacio="Vacío"
          filasEnVivo={[]}
          mensajeVacioEnVivo="Todavía no participaste en sesiones en vivo de esta materia."
        />,
      )

      expect(screen.getByText("Sesiones en vivo")).toBeInTheDocument()
      expect(
        screen.getByText("Todavía no participaste en sesiones en vivo de esta materia."),
      ).toBeInTheDocument()
    })

    it("con filasEnVivo: muestra comisión, cantidad de preguntas, correctas, incorrectas, puntaje y posición", () => {
      const filasEnVivo: FilaSesionEnVivo[] = [
        {
          sesionId: "s1",
          comisionHorario: "Lunes 14-16hs",
          finalizadaEn: "2026-09-20T10:00:00Z",
          cantidadPreguntas: 10,
          cantidadCorrectas: 7,
          cantidadIncorrectas: 4,
          puntajeFinal: 1200,
          posicion: 3,
          totalParticipantes: 14,
        },
      ]

      render(
        <DesempenoResumenDetalle
          desempeno={DESEMPENO}
          filas={FILAS}
          mensajeVacio="Vacío"
          filasEnVivo={filasEnVivo}
          mensajeVacioEnVivo="Vacío en vivo"
        />,
      )

      expect(screen.getByText("Lunes 14-16hs")).toBeInTheDocument()
      expect(screen.getByText(/10 preguntas/)).toBeInTheDocument()
      expect(screen.getByText("7 ✓")).toBeInTheDocument()
      expect(screen.getByText("4 ✗")).toBeInTheDocument()
      expect(screen.getByText("1200 pts")).toBeInTheDocument()
      expect(screen.getByText("3° de 14")).toBeInTheDocument()
    })

    it("período abierto vacío pero con sesiones en vivo: igual muestra la sección de sesiones en vivo", () => {
      render(
        <DesempenoResumenDetalle
          desempeno={DESEMPENO}
          filas={[]}
          mensajeVacio="Todavía no hay evaluaciones."
          filasEnVivo={[sesionEnVivo("s1", "2026-09-20T10:00:00Z")]}
          mensajeVacioEnVivo="Vacío en vivo"
        />,
      )

      expect(screen.getByText("Todavía no hay evaluaciones.")).toBeInTheDocument()
      expect(screen.getByText("Sesiones en vivo")).toBeInTheDocument()
      expect(screen.getByText("Lunes 14-16hs")).toBeInTheDocument()
    })

    it("sin onFilaClick: una fila de sesión en vivo no es clicable (solo lectura)", () => {
      render(
        <DesempenoResumenDetalle
          desempeno={DESEMPENO}
          filas={FILAS}
          mensajeVacio="Vacío"
          filasEnVivo={[sesionEnVivo("s1", "2026-09-20T10:00:00Z")]}
          mensajeVacioEnVivo="Vacío en vivo"
        />,
      )

      expect(screen.queryByRole("button", { name: /Lunes 14-16hs/ })).not.toBeInTheDocument()
    })
  })
})

describe("armarFilasEnVivo", () => {
  it("ordena de la sesión más reciente a la más antigua", () => {
    const masAntigua = sesionEnVivo("s1", "2026-09-01T10:00:00Z")
    const masReciente = sesionEnVivo("s2", "2026-09-10T10:00:00Z")
    const desempeno: DesempenoEstudianteResponse = {
      ...DESEMPENO,
      sesionesEnVivo: [masAntigua, masReciente],
    }

    const filas = armarFilasEnVivo(desempeno)

    expect(filas.map((f) => f.sesionId)).toEqual(["s2", "s1"])
  })

  it("sin sesiones en vivo: devuelve lista vacía", () => {
    expect(armarFilasEnVivo(DESEMPENO)).toEqual([])
  })
})
