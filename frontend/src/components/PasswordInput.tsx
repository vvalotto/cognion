import { Eye, EyeOff } from "lucide-react"
import { useState, type ComponentProps } from "react"

import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

type Fortaleza = "debil" | "media" | "fuerte"

const ETIQUETA_FORTALEZA: Record<Fortaleza, string> = {
  debil: "Débil",
  media: "Media",
  fuerte: "Fuerte",
}
const COLOR_TEXTO_FORTALEZA: Record<Fortaleza, string> = {
  debil: "text-red-600",
  media: "text-amber-600",
  fuerte: "text-emerald-700",
}
const COLOR_BARRA_FORTALEZA: Record<Fortaleza, string> = {
  debil: "bg-red-600",
  media: "bg-amber-600",
  fuerte: "bg-emerald-700",
}

interface Regla {
  cumple: boolean
  etiqueta: string
}

/** Evalúa las 4 reglas de INV-ID-11 ampliada (`US-ADJ-36`) sobre una contraseña en claro. */
function evaluarReglas(password: string): Regla[] {
  return [
    { cumple: password.length >= 12, etiqueta: "Mínimo 12 caracteres" },
    { cumple: /[A-Z]/.test(password), etiqueta: "Una mayúscula" },
    { cumple: /[0-9]/.test(password), etiqueta: "Un número" },
    { cumple: /[^A-Za-z0-9]/.test(password), etiqueta: "Un símbolo" },
  ]
}

function calcularFortaleza(reglasCumplidas: number): Fortaleza {
  if (reglasCumplidas >= 4) return "fuerte"
  if (reglasCumplidas >= 2) return "media"
  return "debil"
}

/** `Input` de contraseña con botón de mostrar/ocultar (`US-ADJ-35`) y, opcionalmente,
 * indicador de fortaleza + checklist de reglas (`US-ADJ-36`, INV-ID-11 ampliada) — mismo
 * lenguaje visual que `Input`, sin perder el valor tipeado al alternar
 * `type="password"`/`type="text"`. */
function PasswordInput({
  className,
  mostrarFortaleza = false,
  ...props
}: Omit<ComponentProps<typeof Input>, "type"> & { mostrarFortaleza?: boolean }) {
  const [visible, setVisible] = useState(false)
  const Icon = visible ? EyeOff : Eye
  const label = visible ? "Ocultar contraseña" : "Mostrar contraseña"
  const valorActual = typeof props.value === "string" ? props.value : ""
  const reglas = mostrarFortaleza ? evaluarReglas(valorActual) : []
  const fortaleza = calcularFortaleza(reglas.filter((r) => r.cumple).length)

  return (
    <div>
      <div className="relative">
        <Input
          type={visible ? "text" : "password"}
          data-slot="password-input"
          className={cn("pr-9", className)}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          title={label}
          aria-label={label}
          className="absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
        >
          <Icon className="size-4" />
        </button>
      </div>
      {mostrarFortaleza && (
        <div className="mt-1.5" data-slot="password-strength">
          <div className="flex gap-1">
            {(["debil", "media", "fuerte"] as const).map((nivel, i) => {
              const nivelesOrden: Fortaleza[] = ["debil", "media", "fuerte"]
              const activo = nivelesOrden.indexOf(fortaleza) >= i
              return (
                <div
                  key={nivel}
                  className={cn(
                    "h-1 flex-1 rounded-full bg-muted",
                    activo && COLOR_BARRA_FORTALEZA[fortaleza],
                  )}
                />
              )
            })}
          </div>
          <p className={cn("mt-1 text-xs font-medium", COLOR_TEXTO_FORTALEZA[fortaleza])}>
            {ETIQUETA_FORTALEZA[fortaleza]}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {reglas.map((r, i) => (
              <span key={r.etiqueta} className={r.cumple ? "text-emerald-700" : undefined}>
                {r.cumple ? "✓" : "○"} {r.etiqueta}
                {i < reglas.length - 1 ? " · " : ""}
              </span>
            ))}
          </p>
        </div>
      )}
    </div>
  )
}

export { PasswordInput }
