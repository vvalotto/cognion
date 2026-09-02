import { cva, type VariantProps } from "class-variance-authority"
import type { ComponentProps } from "react"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        "tipo-om": "bg-blue-50 text-blue-800",
        "tipo-vf": "bg-violet-50 text-violet-800",
        "nivel-alto": "bg-red-50 text-red-800",
        "nivel-medio": "bg-amber-50 text-amber-800",
        "nivel-bajo": "bg-green-50 text-green-800",
        "rol-docente": "bg-blue-50 text-blue-800",
        "rol-estudiante": "bg-violet-50 text-violet-800",
        "rol-admin": "bg-orange-50 text-orange-800",
        "estado-activa": "bg-green-50 text-green-800",
        "estado-bloqueada": "bg-red-50 text-red-800",
        "estado-en-curso": "bg-green-50 text-green-800",
        "estado-programada": "bg-amber-50 text-amber-800",
        "estado-cerrada": "bg-red-50 text-red-800",
        "visible-pendiente": "bg-green-50 text-green-800",
        "visible-todavia-no-abrio": "bg-amber-50 text-amber-800",
        "visible-finalizada": "bg-blue-50 text-blue-800",
        "revision-correcta": "bg-green-50 text-green-800",
        "revision-incorrecta": "bg-red-50 text-red-800",
      },
    },
    defaultVariants: {
      variant: "nivel-medio",
    },
  },
)

function Badge({
  className,
  variant,
  ...props
}: ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant, className }))}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
