/** Una regla de la política de contraseñas (INV-ID-11 ampliada, `US-ADJ-36`) y si la cumple el texto evaluado. */
export interface ReglaPassword {
  cumple: boolean
  etiqueta: string
}

/** Evalúa las 4 reglas de INV-ID-11 ampliada sobre una contraseña en claro. */
export function evaluarReglasPassword(password: string): ReglaPassword[] {
  return [
    { cumple: password.length >= 12, etiqueta: "Mínimo 12 caracteres" },
    { cumple: /[A-Z]/.test(password), etiqueta: "Una mayúscula" },
    { cumple: /[0-9]/.test(password), etiqueta: "Un número" },
    { cumple: /[^A-Za-z0-9]/.test(password), etiqueta: "Un símbolo" },
  ]
}

/** `true` si la contraseña cumple las 4 reglas; el backend las vuelve a aplicar. */
export function cumpleReglasPassword(password: string): boolean {
  return evaluarReglasPassword(password).every((regla) => regla.cumple)
}
