import { Eye, EyeOff } from "lucide-react"
import { useState, type ComponentProps } from "react"

import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

/** `Input` de contraseña con botón de mostrar/ocultar (`US-ADJ-35`) — mismo lenguaje visual
 * que `Input`, sin perder el valor tipeado al alternar `type="password"`/`type="text"`. */
function PasswordInput({ className, ...props }: Omit<ComponentProps<typeof Input>, "type">) {
  const [visible, setVisible] = useState(false)
  const Icon = visible ? EyeOff : Eye
  const label = visible ? "Ocultar contraseña" : "Mostrar contraseña"

  return (
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
  )
}

export { PasswordInput }
