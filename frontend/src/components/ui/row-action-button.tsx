import type { ComponentProps } from "react"

import { Button, buttonVariants } from "@/components/ui/button"
import type { VariantProps } from "class-variance-authority"

/** Botón de ícono para una acción de fila de tabla (Ver/Editar/Eliminar/Activar) — mismo
 * ícono + `title` (tooltip nativo) + `aria-label`, en vez de un botón de texto por acción. */
function RowActionButton({
  label,
  icon: Icon,
  variant = "outline",
  ...props
}: {
  label: string
  icon: React.ComponentType<{ className?: string }>
} & Omit<ComponentProps<typeof Button>, "size" | "children" | "variant" | "className"> &
  Pick<VariantProps<typeof buttonVariants>, "variant">) {
  return (
    <Button type="button" variant={variant} size="icon-sm" title={label} aria-label={label} {...props}>
      <Icon />
    </Button>
  )
}

export { RowActionButton }
