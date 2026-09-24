import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { SEGUNDOS_HISTOGRAMA, StageHistograma } from "./StageHistograma"
import { vistaResultado } from "./_vista-test"

describe("StageHistograma", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    cleanup()
  })

  it("una barra por opción con su cantidad; la correcta con borde blanco y ✓", () => {
    render(<StageHistograma vista={vistaResultado()} onVerRanking={() => {}} />)

    const filas = screen.getAllByRole("listitem")
    expect(filas).toHaveLength(4)
    expect(screen.getAllByTestId("barra-histograma").map((b) => b.textContent)).toEqual([
      "1",
      "3",
      "0",
      "0",
    ])
    expect(filas[1]).toHaveAttribute("data-correcta", "true")
    expect(filas[1]).toHaveTextContent("DIP ✓")
    expect(filas[1].querySelector("span")?.className).toContain("outline-white")
    expect(filas[0]).toHaveAttribute("data-correcta", "false")
    expect(filas[0]).not.toHaveTextContent("✓")
  })

  it("la opción que nadie eligió aparece con barra de 0", () => {
    render(<StageHistograma vista={vistaResultado()} onVerRanking={() => {}} />)
    const barras = screen.getAllByTestId("barra-histograma")
    expect(barras[3]).toHaveTextContent("0")
    expect(barras[3]).toHaveStyle({ width: "0%" })
    expect(barras[1]).toHaveStyle({ width: "100%" })
  })

  it("pasa solo al ranking a los 6 segundos", () => {
    const onVerRanking = vi.fn()
    render(<StageHistograma vista={vistaResultado()} onVerRanking={onVerRanking} />)

    act(() => {
      vi.advanceTimersByTime(SEGUNDOS_HISTOGRAMA * 1000 - 100)
    })
    expect(onVerRanking).not.toHaveBeenCalled()
    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(onVerRanking).toHaveBeenCalledTimes(1)
  })

  it("'Ver ranking ahora' lo adelanta", () => {
    const onVerRanking = vi.fn()
    render(<StageHistograma vista={vistaResultado()} onVerRanking={onVerRanking} />)

    fireEvent.click(screen.getByRole("button", { name: /Ver ranking ahora/ }))
    expect(onVerRanking).toHaveBeenCalledTimes(1)
  })

  it("al desmontar cancela el paso automático", () => {
    const onVerRanking = vi.fn()
    const { unmount } = render(<StageHistograma vista={vistaResultado()} onVerRanking={onVerRanking} />)
    unmount()
    act(() => {
      vi.advanceTimersByTime(10_000)
    })
    expect(onVerRanking).not.toHaveBeenCalled()
  })

  it("sin resultado no dibuja barras", () => {
    render(<StageHistograma vista={vistaResultado({ resultado: null })} onVerRanking={() => {}} />)
    expect(screen.queryAllByTestId("barra-histograma")).toHaveLength(0)
  })
})
