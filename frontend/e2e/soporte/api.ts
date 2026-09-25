import { API, PASSWORD } from "./datos"

/** Llamada a la API real — solo para sembrar datos y verificar lo que la UI no muestra. */
export async function api<T = unknown>(
  metodo: string,
  ruta: string,
  token?: string,
  cuerpo?: unknown,
): Promise<{ status: number; body: T }> {
  const respuesta = await fetch(`${API}${ruta}`, {
    method: metodo,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  })
  const texto = await respuesta.text()
  return { status: respuesta.status, body: (texto ? JSON.parse(texto) : null) as T }
}

export async function login(email: string): Promise<string> {
  const { status, body } = await api<{ access_token: string }>("POST", "/identidad/login", undefined, {
    email,
    password: PASSWORD,
  })
  if (status !== 200) throw new Error(`login ${email}: HTTP ${status}`)
  return body.access_token
}

/** `sub` del JWT — el id del usuario. */
export function idDeToken(token: string): string {
  return JSON.parse(Buffer.from(token.split(".")[1], "base64url").toString()).sub as string
}

interface EstadoApi {
  estado: "EnEspera" | "EnCurso" | "Finalizada"
  opciones_mostradas: boolean
  pregunta_actual_cerrada: boolean
}

/**
 * Deja finalizadas por API todas las sesiones abiertas de la Comisión — para que un circuito que falla
 * a mitad de camino no contamine los siguientes (las tarjetas del Estudiante se buscan por materia).
 */
export async function finalizarSesionesAbiertas(comisionId: string, token: string) {
  const { body: sesiones } = await api<{ id: string; estado: string }[]>(
    "GET",
    `/sesiones-en-vivo?comision_id=${comisionId}`,
    token,
  )
  for (const sesion of sesiones ?? []) {
    if (sesion.estado === "Finalizada") continue
    const base = `/sesiones-en-vivo/${sesion.id}`
    if (sesion.estado === "EnEspera") await api("POST", `${base}/iniciar`, token)
    const { body: estado } = await api<EstadoApi>("GET", base, token)
    if (!estado.opciones_mostradas) await api("POST", `${base}/mostrar-opciones`, token)
    if (!estado.pregunta_actual_cerrada) await api("POST", `${base}/cerrar-pregunta`, token)
    await api("POST", `${base}/finalizar`, token)
  }
}
