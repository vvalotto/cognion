import { useCallback, useEffect, useRef, useState } from "react"

/**
 * Mensaje de error de un formulario que, al aparecer, se desplaza a la vista y recibe el foco.
 *
 * En un celular el botón de enviar está debajo del pliegue y el recuadro de error queda arriba, fuera de
 * pantalla: sin esto el estudiante toca "Crear cuenta" y parece que no pasó nada (spike #595). Un contador
 * hace que repetir el mismo mensaje también vuelva a enfocarlo.
 */
export function useErrorEnfocado() {
  const [estado, setEstado] = useState<{ mensaje: string; veces: number } | null>(null)
  const alertaRef = useRef<HTMLDivElement>(null)

  const setError = useCallback((mensaje: string | null) => {
    setEstado((previo) => (mensaje === null ? null : { mensaje, veces: (previo?.veces ?? 0) + 1 }))
  }, [])

  useEffect(() => {
    if (!estado) return
    alertaRef.current?.scrollIntoView?.({ block: "center", behavior: "smooth" })
    alertaRef.current?.focus()
  }, [estado])

  return { error: estado?.mensaje ?? null, setError, alertaRef }
}
