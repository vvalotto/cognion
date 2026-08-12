interface LogoProps {
  size?: number
  className?: string
}

/** Marca de Cognión (§1 `wireframes-identidad.md`, prototipo aprobado US-1.0.2). */
export function Logo({ size = 44, className }: LogoProps) {
  return (
    <svg
      viewBox="0 0 44 44"
      width={size}
      height={size}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Cognión"
      className={className}
    >
      <circle cx="22" cy="22" r="22" fill="#1d75b5" />
      <path
        d="M8 19c3-3 6-3 9 0s6 3 9 0 6-3 9 0"
        stroke="#ffffff"
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M8 26c3-3 6-3 9 0s6 3 9 0 6-3 9 0"
        stroke="#53aa74"
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  )
}
