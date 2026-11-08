/** Motivo por el que un link de invitación no sirve; decide el texto de `RegistroError` (`US-ADJ-67`). */
export type MotivoInvitacion = "vencida" | "revocada" | "usada" | "invalida"

const MOTIVO_POR_CODIGO: Record<string, MotivoInvitacion> = {
  invitacion_vencida: "vencida",
  invitacion_revocada: "revocada",
  invitacion_usada: "usada",
  invitacion_invalida: "invalida",
}

/** Lee `detail.codigo` de la respuesta del servidor; sin código reconocible, el link "no es correcto". */
export function motivoDeInvitacion(detail: unknown): MotivoInvitacion {
  if (typeof detail === "object" && detail !== null && "codigo" in detail) {
    const codigo = (detail as { codigo: unknown }).codigo
    if (typeof codigo === "string" && codigo in MOTIVO_POR_CODIGO) return MOTIVO_POR_CODIGO[codigo]
  }
  return "invalida"
}

/** `true` si el servidor rechazó el registro por la contraseña y no por el link. */
export function esErrorDePassword(detail: unknown): boolean {
  return (
    typeof detail === "object" &&
    detail !== null &&
    "codigo" in detail &&
    (detail as { codigo: unknown }).codigo === "password_invalida"
  )
}
