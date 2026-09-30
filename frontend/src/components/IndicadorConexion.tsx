import type { EstadoCanal } from "@/lib/canal-sesion-en-vivo"

/** Chip discreto "Reconectando…" (H8) — nunca bloquea ni oculta contenido. */
export function IndicadorConexion({ estado }: { estado: EstadoCanal }) {
  if (estado !== "reconectando") return null
  return (
    <span
      role="status"
      className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800"
    >
      Reconectando…
    </span>
  )
}
