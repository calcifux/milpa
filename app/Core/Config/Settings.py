"""Configuración central tipada (pydantic-settings). El .env es la ÚNICA fuente
de verdad de secretos/config por-entorno; infraestructura va SIN default
(obligatoria) para fallar claro si falta.
"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default local para lo ENCOLADO (broker y lock) cuando no se configura nada. Es solo
# un FALLBACK de conveniencia para dev; no asumimos que siempre haya redis (los flujos
# síncronos no lo tocan). El config expone BROKER_URL/LOCK_URL (agnósticos), no un
# "REDIS_URL" redis-específico.
_DEFAULT_LOCAL_REDIS = "redis://localhost:6379/0"


def _host_timezone() -> str:
    """IANA timezone del HOST — el default cuando no se define TIMEZONE en .env.

    El framework NO impone zona horaria: es responsabilidad del dev/devops fijar
    TIMEZONE explícito (importante sobre todo si quien monta la app no es quien la
    programa — un server suele estar en UTC). Cae a 'UTC' si no se puede detectar.
    """
    try:
        import tzlocal

        return str(tzlocal.get_localzone_name() or "UTC")
    except Exception:
        return "UTC"


class Settings(BaseSettings):
    # extra="ignore": varios módulos comparten el mismo .env; cada Settings
    # ignora las variables que no declara.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Infraestructura / secretos: OBLIGATORIOS (sin default) ---
    database_url: str

    # --- Colas / broker-agnostic (ver docs/research/broker_agnostic_plan.md) ---
    # BROKER de Celery: CUALQUIER transporte (redis://, amqp:// RabbitMQ, sqs://, ...).
    # Vacío => redis local por default. Solo se usa para lo ENCOLADO (los flujos
    # síncronos no lo tocan). ActiveMQ NO es compatible (AMQP 1.0).
    broker_url: str = ""
    # Result backend: OPCIONAL. Nuestros crons son fire-and-forget, así que por default
    # NO hay backend (vacío). Ponlo solo si necesitas leer resultados (AsyncResult).
    result_backend_url: str = ""
    # Store de LOCKS para without_overlapping: redis da `.lock()`, los MQ no. Va aparte
    # del broker (un redis chico basta). Vacío => redis local por default.
    lock_url: str = ""

    # Visibility-timeout (segundos) — SOLO aplica a redis/SQS: si una task no se
    # reconoce en este tiempo, el broker la REENTREGA. El default lock de @cron_task se
    # deriva de aquí para garantizar `lock_timeout > visibility_timeout` por construcción.
    redis_visibility_timeout: int = 3600

    # --- Reintentos de tasks (defaults framework-wide; backoff exponencial con jitter) ---
    # Son los DEFAULTS de `retry_policy(...)` (app/Core/CeleryApp). Se pueden fijar por .env
    # O sobreescribir A MANO en código al declarar cada task. Solo afectan a tasks que OPTAN
    # por reintentar (pasan `autoretry_for`); NUNCA a los crons. 0 => sin reintentos.
    task_max_retries: int = 3
    task_retry_backoff: int = 2  # segundos base del 1er reintento (luego se duplica)
    task_retry_backoff_max: int = 600  # tope del backoff entre reintentos (10 min)

    # --- Operativo ---
    # Default GENÉRICO (Core es reutilizable): cada proyecto pone su APP_NAME en .env.
    app_name: str = "App"
    app_env: str = "qa"  # local | qa | production (como config('app.env') del legacy)
    app_port: int = 8000  # puerto del servidor web (`jornal serve`)
    # Locale de fallback de toda la app (i18n transversal: correos, API, etc.) cuando
    # no se pasa locale explícito. Override en .env con APP_FALLBACK_LOCALE.
    app_fallback_locale: str = "es"
    # Default = zona del HOST (no la imponemos). El dev/devops DEBE fijar TIMEZONE en .env.
    timezone: str = Field(default_factory=_host_timezone)

    # --- HTTP / middlewares (todos coma-separados; defaults SEGUROS) ---
    # CORS: vacío => NO se monta CORS (same-origin, seguro). En dev pon el origin de
    # tu front (p. ej. "http://localhost:3000"). NUNCA "*" con credentials en prod.
    cors_allow_origins: str = ""
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    cors_allow_credentials: bool = False
    # TrustedHost: "*" => off. Fija dominios en prod (anti Host-header attack).
    trusted_hosts: str = "*"
    # GZip: off por default (en prod suele hacerse mejor en nginx/proxy).
    gzip_enabled: bool = False
    gzip_min_size: int = 500

    # --- HTTP / security headers (defensivos; defaults SEGUROS, todo apagable) ---
    # Trío seguro (nosniff + X-Frame-Options + Referrer-Policy): ON por default (downside ~0).
    security_headers_enabled: bool = True
    security_frame_options: str = "DENY"  # DENY | SAMEORIGIN | "" (no mandar)
    security_referrer_policy: str = "no-referrer"
    # HSTS: fuerza HTTPS en el navegador. OFF por default (solo tiene sentido sirviendo
    # HTTPS; encenderlo mal "encierra" al cliente en https). Actívalo en prod tras TLS.
    hsts_enabled: bool = False
    hsts_max_age: int = 31536000  # 1 año (segundos)
    hsts_include_subdomains: bool = True
    # CSP: vacío => no se manda (es ESPECÍFICO de cada app; un CSP malo rompe la página).
    content_security_policy: str = ""

    # --- Correo (fallback de destinatarios cuando system_config no tiene el name) ---
    admin_system_mails: str = ""  # coma-separado; = config('constants.admin_system_mails')
    mail_cco_recipient: str = ""  # = config('constants.mail_cco_recipient')

    # --- Correo (equivalente a config('mail.*') del legacy) ---
    # En local apuntan a Mailpit (localhost:1025); en QA/prod al SMTP corporativo.
    # MAIL_DRIVER (= mail.default de Laravel): cómo se MANDA.
    #   "smtp" (default) -> envía por SMTP real.
    #   "log"            -> NO envía: escribe el correo en el log (dev/sin SMTP; cross-platform).
    #   "null"/"array"   -> no-op: descarta el correo (tests / silenciar).
    mail_driver: str = "smtp"
    mail_host: str = "localhost"
    mail_port: int = 1025
    mail_username: str = ""
    mail_password: str = ""
    mail_encryption: str = ""  # "" (sin cifrado, ej. Mailpit) | "tls" (STARTTLS) | "ssl" (SMTPS)
    # Remitente. Aceptamos el nombre de Laravel (MAIL_FROM_ADDRESS) y el natural.
    mail_from_email: str = Field(
        default="no-reply@example.com",
        validation_alias=AliasChoices("MAIL_FROM_ADDRESS", "MAIL_FROM_EMAIL"),
    )
    mail_from_name: str = "App"
    # Compartimos BD con esquema legacy: NUNCA crear/alterar tablas solos.
    auto_create_tables: bool = False

    # --- Auth: llave pública de Passport (RS256) ---
    passport_public_key: str | None = None
    passport_public_key_path: str | None = None
    passport_expected_audience: str | None = None

    # --- Logging (Loguru) ---
    log_level: str = "INFO"
    log_json: bool = False
    log_dir: str = "logs"

    @property
    def effective_broker_url(self) -> str:
        """Broker de Celery; cae al redis local por default si BROKER_URL está vacío."""
        return self.broker_url or _DEFAULT_LOCAL_REDIS

    @property
    def effective_lock_url(self) -> str:
        """Store de locks (redis); cae al redis local por default si LOCK_URL está vacío."""
        return self.lock_url or _DEFAULT_LOCAL_REDIS

    @property
    def effective_result_backend(self) -> str | None:
        """Result backend; None (sin backend) por default — crons fire-and-forget."""
        return self.result_backend_url or None

    @property
    def broker_uses_visibility_timeout(self) -> bool:
        """visibility_timeout solo aplica a redis/SQS (no a RabbitMQ/AMQP, etc.)."""
        return self.effective_broker_url.startswith(("redis://", "rediss://", "sqs://"))

    def load_passport_public_key(self) -> str | None:
        if self.passport_public_key:
            return self.passport_public_key
        if self.passport_public_key_path:
            with open(self.passport_public_key_path, encoding="utf-8") as file:
                return file.read()
        return None


settings = Settings()
