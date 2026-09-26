import { vi } from "vitest"

export const MATERIAS_TEST = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 0, activa: true },
]

const ES_LISTADO_MATERIAS = /\/materias(\?[^/]*)?$/

function json(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } })
}

/**
 * Mock de `fetch` para las pantallas de Comisión, que piden `GET /materias` para el breadcrumb
 * (`useNombreMateria`): ese pedido se responde por URL y el resto con `respuestas`, en orden.
 */
export function fetchConMaterias(respuestas: Response[], materias: unknown[] = MATERIAS_TEST) {
  const cola = [...respuestas]
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    if (ES_LISTADO_MATERIAS.test(String(input)) && (!init?.method || init.method === "GET")) {
      return json(materias)
    }
    const respuesta = cola.shift()
    if (!respuesta) throw new Error(`fetch inesperado: ${String(input)}`)
    return respuesta
  })
}

/** Llamadas a `fetch` sin contar las de `GET /materias` del breadcrumb. */
export function llamadasSinMaterias() {
  return vi.mocked(fetch).mock.calls.filter(([url]) => !ES_LISTADO_MATERIAS.test(String(url)))
}
