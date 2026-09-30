import { useEffect, useState } from "react"

const INTERVALO_MS = 250

/** Segundos que le quedan a la pregunta, acotados a ≥ 0 (informativo: el corte real es del servidor). */
export function segundosRestantes(limiteSegundos: number, inicioMs: number, ahoraMs: number): number {
  const transcurridos = (ahoraMs - inicioMs) / 1000
  return Math.max(0, Math.ceil(limiteSegundos - transcurridos))
}

export function formatearTemporizador(segundos: number): string {
  const minutos = Math.floor(segundos / 60)
  const resto = segundos % 60
  return `${String(minutos).padStart(2, "0")}:${String(resto).padStart(2, "0")}`
}

/** Cuenta regresiva que se recalcula contra el reloj — no cierra nada al llegar a 0. */
export function useSegundosRestantes(limiteSegundos: number, inicioMs: number): number {
  const [ahora, setAhora] = useState(() => Date.now())

  useEffect(() => {
    setAhora(Date.now())
    const intervalo = setInterval(() => setAhora(Date.now()), INTERVALO_MS)
    return () => clearInterval(intervalo)
  }, [limiteSegundos, inicioMs])

  return segundosRestantes(limiteSegundos, inicioMs, ahora)
}
