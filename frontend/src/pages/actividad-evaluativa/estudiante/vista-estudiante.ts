import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import type { EstadoSesionEnVivoResponse } from "@/lib/sesion-en-vivo-api"

/** `pregunta` y `finalizada` las completa `US-6.3.9` sobre este mismo contenedor. */
export type EtapaEstudiante = "sala" | "pregunta" | "finalizada"

export interface VistaEstudiante {
  etapa: EtapaEstudiante
  totalParticipantes: number
}

/** Etapa que le corresponde al estado del servidor. */
export function calcularVistaEstudiante(estado: EstadoSesionEnVivoResponse): VistaEstudiante {
  const etapa: EtapaEstudiante =
    estado.estado === "en_espera" ? "sala" : estado.estado === "en_curso" ? "pregunta" : "finalizada"
  return { etapa, totalParticipantes: estado.totalParticipantes }
}

/** Aplica un mensaje del canal; los que esta etapa no usa se ignoran. */
export function aplicarMensajeEstudiante(
  vista: VistaEstudiante,
  mensaje: MensajeSesionEnVivo,
): VistaEstudiante {
  switch (mensaje.tipo) {
    case "participantes_actualizados":
      return { ...vista, totalParticipantes: mensaje.cantidad }
    case "pregunta_presentada":
      return vista.etapa === "finalizada" ? vista : { ...vista, etapa: "pregunta" }
    case "sesion_finalizada":
      return { ...vista, etapa: "finalizada" }
    default:
      return vista
  }
}
