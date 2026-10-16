"""Configuración de la aplicación cargada desde variables de entorno."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de configuración leídos de `.env` o del entorno del proceso."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-responder@cognion.local"
    verificador_vencimientos_cadencia_segundos: int = 120
    verificador_vencimientos_umbral_inactividad_minutos: int = 15
    administrador_bloqueo_temporal_minutos: int = 15
    frontend_url: str = "http://localhost:5173"
    cors_allowed_origins: str = "http://localhost:5173"

    @field_validator("cors_allowed_origins")
    @classmethod
    def _rechazar_origen_comodin(cls, valor: str) -> str:
        """Rechaza `*`: es incompatible con `allow_credentials=True` en CORS."""
        if "*" in [origen.strip() for origen in valor.split(",")]:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS no admite '*' porque la API usa credenciales; "
                "listar los orígenes explícitos separados por coma"
            )
        return valor

    @property
    def cors_origins_list(self) -> list[str]:
        """Orígenes CORS permitidos, separados por coma, sin espacios ni vacíos."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


settings = Settings()
