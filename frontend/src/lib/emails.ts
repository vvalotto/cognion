/**
 * `true` si los dos emails escritos son el mismo: se comparan sin espacios en los bordes y sin distinguir
 * mayúsculas (`wireframes-identidad-autoservicio.md` §5.2, hallazgo #5 de la UAT de `v0.9.0`).
 */
export function emailsCoinciden(email: string, repetido: string): boolean {
  return email.trim().toLowerCase() === repetido.trim().toLowerCase()
}
