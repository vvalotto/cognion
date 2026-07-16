# shared

> Única excepción transversal a la regla de "sin imports directos entre BCs" — ver
> CLAUDE.md raíz §Arquitectura interna.

Contiene únicamente tipos y utilidades sin lógica de negocio de un BC específico
(ej. value objects genéricos, tipos base). No es un lugar para lógica compartida "por
conveniencia" — si un tipo pertenece a un BC, vive en `src/<bc>/entities/`, no acá.

Cualquier BC puede importar de `src/shared/entities/`. Ningún otro import cruzado entre
`src/<bc>/` está permitido — la comunicación entre BCs pasa por puertos en
`entities/ports/`.
