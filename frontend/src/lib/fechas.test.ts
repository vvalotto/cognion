import { describe, expect, it } from "vitest"

import { aIsoConZona } from "./fechas"

describe("aIsoConZona", () => {
  it("devuelve el mismo instante que la hora local escrita, con zona", () => {
    const iso = aIsoConZona("2026-10-25T14:00")
    expect(iso.endsWith("Z")).toBe(true)
    // La hora de pared 14:00 del navegador es exactamente ese instante, en cualquier zona horaria.
    expect(new Date(iso).getTime()).toBe(new Date(2026, 9, 25, 14, 0).getTime())
  })

  it("no cambia la hora de pared al volver a mostrarla en el navegador", () => {
    const iso = aIsoConZona("2026-10-25T09:54")
    const vuelta = new Date(iso)
    expect([vuelta.getHours(), vuelta.getMinutes()]).toEqual([9, 54])
  })

  it("conserva el día cuando la hora local cruza la medianoche en UTC", () => {
    const iso = aIsoConZona("2026-12-31T23:30")
    const vuelta = new Date(iso)
    expect([vuelta.getFullYear(), vuelta.getMonth(), vuelta.getDate()]).toEqual([2026, 11, 31])
  })

  it("rechaza un valor que no es una fecha", () => {
    expect(() => aIsoConZona("no-es-una-fecha")).toThrow(RangeError)
  })
})
