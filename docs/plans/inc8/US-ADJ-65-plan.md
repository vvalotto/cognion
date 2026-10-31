# Plan de Implementación: US-ADJ-65 - El comando que crea el Administrador pide la contraseña dos veces

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** Identidad · **Capa:** `frameworks/cli`

## Diseño
Hoy `bootstrap_administrador` llama a `getpass.getpass` una sola vez. Un error de tipeo (la contraseña no se ve) crea un Administrador inaccesible, que fue lo que pasó en la UAT de `v0.9.0`. La corrección es solo del comando: el dominio y el caso de uso no cambian.

```
pedir_password_confirmada(leer, avisar) ── hasta 3 intentos ──▶ contraseña confirmada
        │                                     └─ 3 desencuentros ─▶ ContrasenasNoCoinciden
        ▼
ejecutar(env, pedir_password, repositorio, hasher)
   1. faltan ADMIN_NOMBRE/ADMIN_EMAIL        → código 1 (igual que hoy)
   2. ya hay un Administrador operativo      → mensaje y código 0, SIN pedir la contraseña   ← nuevo
   3. contraseña = ADMIN_PASSWORD o terminal → sin terminal ni variable: código 2 (igual que hoy)
   4. ContrasenasNoCoinciden                 → código 1, sin crear nada                       ← nuevo
   5. caso de uso (INV-ID-11, email en uso)  → mensajes y códigos de siempre
```

- `pedir_password_confirmada` recibe cómo leer y cómo avisar: la terminal real le pasa `getpass.getpass` y `print`; los tests, entradas guiadas.
- El caso de uso conserva su comprobación de "ya existe un Administrador" (defensa ante una carrera); la consulta previa del comando solo evita pedir la contraseña de más.
- `ADMIN_PASSWORD` y "sin terminal" no cambian.

## Componentes a Implementar

### 1. Comando (`src/identidad/frameworks/cli/bootstrap_administrador.py`)
- [ ] Constante `MAX_INTENTOS_PASSWORD = 3` y excepción `ContrasenasNoCoinciden`.
- [ ] `pedir_password_confirmada(leer, avisar) -> str`: pide "Contraseña del Administrador:" y "Repetí la contraseña:"; si no coinciden avisa "Las contraseñas no coinciden." (y cuántos intentos quedan) y vuelve a pedir; al tercer desencuentro levanta `ContrasenasNoCoinciden`.
- [ ] `pedir_password_por_terminal()`: sin terminal interactiva devuelve `None` (igual que hoy); con terminal usa `pedir_password_confirmada(getpass.getpass, print)`.
- [ ] `ejecutar`: consulta `repositorio.contar_administradores_operativos()` antes de pedir la contraseña; atrapa `ContrasenasNoCoinciden` y devuelve `SALIDA_ENTRADA_INVALIDA` con un mensaje que dice que no se creó nada.

### 2. Integración
- [ ] Sin cambios en dominio, casos de uso, repositorios, `levantar.sh` ni frontend. `levantar.sh` ya invoca el comando de forma interactiva y hereda la confirmación.
- [ ] Documentación (Fase 8): `DESPLIEGUE-LOCAL.md` §4 paso 5 y `ADR-016` (nota breve).

## Tests (Fases 4 a 6)
- **Unitarios:** `pedir_password_confirmada` (coinciden, desencuentro y luego acierto, tres desencuentros, mensaje con intentos restantes); `ejecutar` (los 7 escenarios con repositorio y hasher falsos, contando cuántas veces se pidió la contraseña); regresiones de `US-8.1.5` sin tocar.
- **Integración:** el comando bajo una **terminal simulada** (`pty.fork()`, biblioteca estándar) contra una base descartable: se escribe dos veces la contraseña, y una vez con desencuentro. Prueba lo que los falsos no pueden: que `getpass` real pida dos veces y que el Administrador quede creado y pueda iniciar sesión.
- **BDD:** los 7 escenarios aprobados.

## Riesgos
- **El test con `pty` puede ser frágil** (temporización, lectura de la salida): se lee hasta ver cada texto de pedido, con tiempo máximo, y se mata el proceso hijo si no termina. Si resultara inestable en CI se marca para correr solo con base descartable, como el resto de la integración.
- **`getpass` solo es "real" con terminal de control**: por eso `pty.fork()` y no `subprocess` con un pipe.
- **El mensaje de intentos restantes** no debe revelar la contraseña ni nada derivado de ella.
