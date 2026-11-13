# Modelo de datos — BC Identidad

Ver principios generales y aislamiento cross-BC en `24-modelo-datos-postgresql.md`.

## Tablas

| Tabla | Rol |
|-------|-----|
| `usuario` | Base común de toda cuenta — email, hash de password, estado de bloqueo |
| `administrador` | Marca de perfil sobre `usuario` (tabla vacía salvo la FK/PK) |
| `docente` | Marca de perfil sobre `usuario` |
| `estudiante` | Marca de perfil sobre `usuario`, con su comisión asignada |
| `comision` | Comisión de una materia, con horario y docentes asignados |
| `comision_docentes` | Tabla puente N:M entre `comision` y `docente` |
| `invitacion` | Link de registro emitido por un Docente para una Comisión: individual (un uso) o **grupal** (varios usos hasta que vence o se revoca, `ADR-027`) |
| `token_recuperacion_password` | Token de un solo uso para recuperación de contraseña |

## Patrón "marca de perfil" (table-per-subclass manual)

`administrador`, `docente` y `estudiante` no son subclases de SQLAlchemy — son tablas
independientes cuya **PK es también FK a `usuario.id`**:

```python
class DocenteModel(Base):
    __tablename__ = "docente"
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuario.id"), primary_key=True)
```

Una fila en `docente` con `id = X` es un "marcador" de que el `usuario` `X` tiene perfil
Docente. `estudiante` extiende el patrón con una columna propia (`comision_id`), porque un
Estudiante necesita saber a qué Comisión pertenece (INV-ID-05: un Estudiante cursa una única
Comisión — sin muchos-a-muchos, limitación documentada en `CLAUDE.md` §Incremento 4).

## Diagrama ER

```mermaid
erDiagram
    USUARIO ||--o| ADMINISTRADOR : "perfil"
    USUARIO ||--o| DOCENTE : "perfil"
    USUARIO ||--o| ESTUDIANTE : "perfil"
    USUARIO ||--o{ TOKEN_RECUPERACION_PASSWORD : emite
    COMISION ||--o{ ESTUDIANTE : inscribe
    COMISION }o--o{ DOCENTE : "comision_docentes"
    COMISION ||--o{ INVITACION : origina
    DOCENTE ||--o{ INVITACION : genera
    ADMINISTRADOR ||--o{ COMISION : crea

    USUARIO {
        uuid id PK
        string nombre
        string email UK
        string password_hash
        bool bloqueada
        int intentos_fallidos_login
        int intentos_fallidos_password
        datetime creado_en
        bool deshabilitada
        datetime bloqueada_hasta "NULL = bloqueo permanente; con valor = temporal"
    }
    ADMINISTRADOR {
        uuid id "PK, FK"
    }
    DOCENTE {
        uuid id "PK, FK"
    }
    ESTUDIANTE {
        uuid id "PK, FK"
        uuid comision_id FK
    }
    COMISION {
        uuid id PK
        uuid materia_id "sin FK real, cross-BC, ver 24-modelo-datos-postgresql.md"
        string horario
        uuid administrador_id FK
        bool activa
    }
    INVITACION {
        uuid id PK
        uuid comision_id FK
        uuid docente_id FK
        string token UK
        datetime generada_en
        datetime expira_en
        datetime usada_en
        bool grupal
        int usos "contador de registros del link grupal"
        datetime revocada_en
    }
    TOKEN_RECUPERACION_PASSWORD {
        uuid id PK
        uuid usuario_id FK
        string token UK
        datetime generado_en
        datetime expira_en
        datetime usado_en
    }
```

## Notas de implementación

- `comision.materia_id` **no tiene `ForeignKey`** en el modelo ORM — apunta a `materia` del BC
  Banco de Preguntas, resuelto vía `MateriaPort` (`US-2.1.2`). Es el único caso de FK "lógica"
  cross-BC de este BC.
- `usuario.email` es único — es el identificador de login.
- `token_recuperacion_password.token` es único y de un solo uso (`usado_en` marca el consumo).
- `invitacion.token` es único. La **individual** es de un solo uso (`usada_en`); la **grupal** (`grupal = true`) admite varios: `usos` se incrementa con un `UPDATE` atómico en la base porque varios estudiantes se registran a la vez, y `revocada_en` la desactiva. Hay a lo sumo un link grupal vigente por comisión (migración `f7a3c9d15e82`).
- `usuario.bloqueada_hasta`: `NULL` con `bloqueada = true` es un bloqueo permanente; con valor es un bloqueo temporal, que hoy solo se aplica al último administrador operativo (migración `c4d1f9a27b60`).
- Contraseña segura (`INV-ID-11` ampliada, `US-ADJ-36`): mínimo 12 caracteres + mezcla de
  tipos, validada en dominio (`Usuario.validar_password_nueva()`), no en el esquema de BD.

## Fuente de verdad

`src/identidad/frameworks/db/models.py`.
