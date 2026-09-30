import { act, renderHook } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  formatearTemporizador,
  segundosRestantes,
  useSegundosRestantes,
} from "@/lib/temporizador-pregunta"

describe("segundosRestantes", () => {
  it("descuenta el tiempo transcurrido", () => {
    expect(segundosRestantes(20, 1_000, 11_000)).toBe(10)
  })

  it("no baja de cero", () => {
    expect(segundosRestantes(20, 1_000, 100_000)).toBe(0)
  })

  it("redondea hacia arriba mientras queda una fracción", () => {
    expect(segundosRestantes(20, 0, 500)).toBe(20)
  })
})

describe("formatearTemporizador", () => {
  it("formatea MM:SS", () => {
    expect(formatearTemporizador(14)).toBe("00:14")
    expect(formatearTemporizador(65)).toBe("01:05")
    expect(formatearTemporizador(0)).toBe("00:00")
  })
})

describe("useSegundosRestantes", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date("2026-09-23T10:00:00Z"))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("cuenta regresiva y se queda en cero", () => {
    const inicio = Date.now()
    const { result } = renderHook(() => useSegundosRestantes(3, inicio))
    expect(result.current).toBe(3)

    act(() => {
      vi.advanceTimersByTime(2000)
    })
    expect(result.current).toBe(1)

    act(() => {
      vi.advanceTimersByTime(10_000)
    })
    expect(result.current).toBe(0)
  })

  it("descuenta el tiempo ya transcurrido si el inicio es anterior", () => {
    const inicio = Date.now() - 10_000
    const { result } = renderHook(() => useSegundosRestantes(30, inicio))
    expect(result.current).toBe(20)
  })
})
