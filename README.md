# milpa

[![CI](https://github.com/calcifux/milpa/actions/workflows/ci.yml/badge.svg)](https://github.com/calcifux/milpa/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.14+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![uv](https://img.shields.io/badge/deps-uv-DE5FE9)
![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)
![Mypy](https://img.shields.io/badge/types-mypy_strict-2A6DB2)
![License](https://img.shields.io/badge/license-MIT-blue)

**milpa** es un microframework de **Python 3.14** para construir **monolitos
modulares**, inspirado en la ergonomía de **Laravel** y la disciplina de capas de
**Spring**. Junta cuatro piezas maduras detrás de una estructura opinada y un kernel
compartido reutilizable:

- **FastAPI** para HTTP, **Celery** para tareas/crons, **SQLAlchemy 2.0** para datos,
  **Typer** para la consola.

Pensado para dos cosas: **arrancar servicios nuevos** sin re-decidir la arquitectura
cada vez, y **migrar apps legacy de Laravel** a Python conservando conceptos familiares
(artisan, scheduler, mailables, soft-deletes, timestamps, Passport).

- **API**: FastAPI (`src/milpa/Core/Http/Http.py:create_app`); descubre los módulos activos.
- **Crons / tareas**: Celery worker + beat (`src/milpa/Core/CeleryApp/CeleryApp.py:celery_app`).
- **CLI** (estilo `artisan`): `jornal` en la raíz (launcher fino del kernel de consola).
- **Infra**: Docker **solo** levanta Redis + Mailpit (+ RabbitMQ opcional); la app
  corre en el host.

> **El kernel (`src/milpa/Core`) es el framework.** Es genérico y reutilizable entre
> proyectos. Lo específico de cada app vive fuera de `Core`: en `app/Modules/*`,
> `app/Models`, `app/Dictionaries`, `app/Resources` y el launcher `jornal`.

## ✨ Características

Todo es **OPT-IN** y auto-descubrible (no estorba si no lo usas):

- **Patrones estilo milpa** — `Events`/`Observers` (1:N, transporte adaptativo: worker si hay
  broker, si no síncrono), `Mediator` (command bus 1:1, transport-neutral HTTP+CLI) y `Pipeline`
  (modelo cebolla). Patrones ya probados que un arquitecto puede sugerir, no impuestos.
- **Background** — `@job` (on-demand, `.dispatch()`) y `@cron_task` (agendado, anti-overlap),
  separados a propósito (job ≠ cron).
- **API REST (estilo DRF)** — versionado (`@Controller(version="v1")`), rate limiting
  (`@rate_limit`), filtering DSL (`FilterQueryModel`) + paginación por cursor, y negociación de
  contenido (una ruta sirve JSON o HTML según `Accept`).
- **Auth** — RBAC (roles) + ABAC (`Gate`/`@policy`), JWT (API) + sesión cookie/CSRF (browser,
  estilo Sanctum); valida también tokens OAuth2 de Laravel Passport.
- **Errores que NUNCA fallan en silencio** — todo error HTTP sale en **RFC 9457**
  (`application/problem+json`); el CLI rinde errores limpios (sin traceback crudo ni fuga de
  valores); mensajes accionables que apuntan al fix.
- **Datos estilo Spring Data** — `Repository[Model, Id]` tipado, `@transactional`, serializers
  Pydantic v2 (`computed_field`), soft-delete y timestamps automáticos; engine agnóstico del motor.
- **HTTP** — controllers class-based (`@Controller`/`@Get`/`@Post`), Jinja2 + HTMX/Alpine (sin
  Inertia) · **i18n** (YAML) · **mail** (`Mailable` + drivers smtp/log/null + plantillas firmadas).
- **Assets con Vite (estilo laravel-vite)** — el helper Jinja `vite('src/main.jsx')` (más
  `vite_asset()` y `vite_react_refresh()`): en **dev** inyecta el cliente HMR desde el dev server
  (vía hot-file por app); en **prod** lee `dist/.vite/manifest.json` y emite `<link>`/`<script>`
  hasheados. milpa es dueño del shell HTML; Vite, del pipeline de assets. Sin apps detectadas no se
  monta nada.
- **Microfrontends por vertical (`surcos/`)** — cada equipo su app Vite en `surcos/<app>` con SU
  tecnología (React/Vue/Svelte/vanilla); milpa sirve todos los shells en el **mismo origen, cero
  CORS**, e inyecta runtime-config (`window.__ENV`, vía `shell_context()`) — lo que `VITE_*`/
  `NEXT_PUBLIC_*` no pueden dar sin rebuild. *Forma tradicional* (cada SPA en su servidor con CORS
  congelado en build-time) vs *estilo milpa* (el backend sirve los shells, mismo origen).
- **PWA sin boilerplate** — `Pwa.webmanifest(request, ...)` y `Pwa.service_worker(...)` como
  one-liners de controller: el manifest se arma **en runtime** (`start_url`/`scope` con el prefijo
  real del deploy) y los iconos se auto-descubren del build por convención.

> Cada feature tiene su página en el [manual](documentation/README.md) y se demuestra ejecutable
> en el **módulo Demo** (contrastando la *forma tradicional* vs *estilo milpa*).

## 📖 Documentación

La guía completa estilo Laravel está en **[`documentation/`](documentation/README.md)**:
instalación, configuración, ciclo de vida HTTP, módulos, consola, correo, colas, cron, jobs,
i18n, autenticación, base de datos (modelos, repositorios, filtrado/paginación), los **patrones
estilo milpa** (eventos/observers, mediator, pipeline), la **API REST** (versionado, rate limiting,
negociación de contenido, serializadores) y los **errores RFC 9457**.

---

## 1. Requisitos

- **Python 3.14+**
- **Docker** + Docker Compose (para Redis y Mailpit en local)
- Una **base de datos** alcanzable (el engine es agnóstico del motor: MySQL/MariaDB,
  PostgreSQL, Oracle, SQL Server, SQLite). Se elige con `DATABASE_URL`.
- (Recomendado) **[uv](https://docs.astral.sh/uv/)** como gestor de entorno y deps.
- **(OPT-IN, solo si usas frontends)** **Node** `>=22.13` (`.nvmrc` fija `22`: pnpm 11 usa `node:sqlite`) y
  **pnpm 11** para el pipeline de assets Vite de los `surcos/`. Si tu proyecto no tiene frontend,
  no necesitas Node ni pnpm.

---

## 2. Instalación

> **Nombre del paquete:** en PyPI se publica como **`milpa-core`** (el nombre `milpa` ya estaba
> tomado); el **import** (`milpa.*`) y el **comando** (`jornal`/`milpa new`) siguen siendo `milpa`.
> Un proyecto generado con `milpa new` depende de `milpa-core` (piso actual: `>=0.4.0`).

### Opción A — con `uv` (recomendada)

```bash
uv sync
```

Eso crea el entorno y resuelve dependencias (incluidas las de dev) desde
`pyproject.toml` / `uv.lock`. Antepón `uv run` a cualquier comando (no necesitas
activar el venv): `uv run pytest`, `uv run python jornal list`, etc.

> Solo producción (sin herramientas de dev): `uv sync --no-dev`.
> Driver de BD según tu motor (extras opcionales): `uv sync --extra postgres`
> (también `oracle`, `mssql`; MySQL/MariaDB ya va en el core).

### Opción B — Python + venv (pip)

```bash
python3.14 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e .                   # dependencias de ejecución
pip install --group dev            # herramientas de dev (pip >= 25.1)
# pip más viejo:  pip install pytest ruff mypy import-linter
```

Con el venv **activado**, corre los comandos **sin** el prefijo `uv run`.

### Frontend (OPT-IN — solo si tienes `surcos/`)

Los microfrontends son un workspace **pnpm** (`pnpm-workspace.yaml`, `packages: surcos/*`):

```bash
pnpm install                       # en la raíz: instala TODOS los surcos de un jalón
pnpm -r build                      # buildea cada surco → public/<app> (lo que sirve milpa en prod)
pnpm --filter <surco> dev          # dev server con HMR de UN surco (escribe su hot-file)
```

> **Workspace sin phantom deps:** pnpm da `node_modules` **por paquete** (symlinks al store
> global), así cada surco solo ve lo que **declara** (la phantom dep truena en dev, no al
> extraer el surco a su propio repo). pnpm 11 no corre postinstall por default (anti
> supply-chain): `allowBuilds` aprueba los explícitos (p. ej. `esbuild`, que Vite necesita).

---

## 3. Configuración (`.env`)

```bash
cp .env.example .env
```

Variables clave (el `.env.example` trae todas, comentadas):

| Variable | Para qué |
|----------|----------|
| `DATABASE_URL` | Conexión SQLAlchemy. Define el motor: `mysql+pymysql://…`, `postgresql+psycopg://…`, `sqlite:///app.db`, … |
| `BROKER_URL` | Transporte de Celery para lo **encolado**. Vacío => Redis local. (`redis://…`, `amqp://…`). |
| `TIMEZONE` | Zona de la app (nombre IANA, ej. `America/Mexico_City`). Gobierna timestamps y cálculos de fecha. |
| `APP_NAME` / `APP_ENV` | Nombre del proyecto y entorno (`local`/`prod`); el env gatea crons y CCO de correo. |
| `APP_PORT` | Puerto del servidor FastAPI. |
| `AUTO_CREATE_TABLES` | Si la app puede crear tablas. Contra una BD legacy: **`false`**. |
| `APP_FALLBACK_LOCALE` | Locale de fallback de i18n (correos, API) cuando no se pasa uno explícito. |
| `MAIL_DRIVER` | `smtp` (real) · `log` (lo escribe en el log, dev sin SMTP) · `null` (no-op). |
| `MAIL_*` | Host/puerto/credenciales/remitente del correo (en local apunta a Mailpit). |
| `CORS_*` / `TRUSTED_HOSTS` / `GZIP_ENABLED` | Middlewares HTTP (defaults seguros si se omiten). |
| `SECURITY_HEADERS_ENABLED` / `HSTS_*` / `CONTENT_SECURITY_POLICY` | Security headers defensivos (nosniff/X-Frame-Options/Referrer-Policy ON; HSTS/CSP opt-in). |
| `AUTH_GUARD` / `JWT_SECRET` / `SESSION_SECRET` | Auth propia: guard por default + secretos del JWT (API) y de la sesión (browser). |
| `PASSPORT_PUBLIC_KEY_PATH` | (Opcional) Llave pública para validar tokens OAuth2 de Laravel Passport (ver §4). |
| `LOG_LEVEL` / `LOG_JSON` | Logging (Loguru). `LOG_JSON=true` agrega `logs/app.jsonl`. |
| `ASSET_URL` | Prefijo público que `asset()`/`vite()` anteponen a sus URLs: CDN (`https://cdn.x.com`) o sub-ruta de reverse proxy. Default vacío. **DEBE coincidir** con el `ASSET_URL` con que se buildea el frontend. |
| `VITE_APPS_DIR` | Carpeta de las fuentes de los microfrontends (un surco = un vertical). Default `surcos`. Es app toda carpeta con `hot` o `dist/.vite/manifest.json`. |
| `VITE_PUBLIC_DIR` | Carpeta donde caen los builds (`vite build` de cada surco → `public/<app>`); milpa la monta completa. Default `public`. |
| `VITE_DIST_DIR` | Override **explícito** para una sola app (frontend en la raíz, estilo Laravel): apunta directo al `dist/` y se ignora la auto-detección. Default vacío. |
| `VITE_HOT_FILE` | Hot-file del modo una-sola-app (con `VITE_DIST_DIR`). Default vacío => `<dist>/../hot`. En multi-app el hot-file es siempre `<app>/hot`. |
| `VITE_ASSETS_URL` | Raíz pública de los assets: cada surco se sirve en `<assets_url>/<app>`. Default `/vite`. **DEBE coincidir** con el `base` del `vite.config`. |

> **Host vs Docker:** si corres la app en el host (lo normal en dev), usa
> `localhost`/`127.0.0.1` en las URLs. El `.env.example` asume Docker y lo aclara.

---

## 4. Secrets (opcional)

La carpeta `secrets/` se versiona vacía (`.gitkeep`); **su contenido lo ignora git**.
Úsala para llaves locales. Caso típico al **migrar desde Laravel**: validar tokens
**OAuth2 de Passport** colocando ahí la llave **pública** RS256 del legacy
(`storage/oauth-public.key`) y apuntando `PASSPORT_PUBLIC_KEY_PATH` a ella.

Nunca subas llaves ni el `.env` al repo.

---

## 5. Levantar la infraestructura (Docker)

Docker **solo** corre infraestructura. La app NO va en Docker.

```bash
docker compose up -d        # Redis + Mailpit (RabbitMQ opcional, ver compose)
```

- **Redis**: `localhost:6379` (broker/lock por default de Celery).
- **Mailpit**: SMTP en `localhost:1025`; **UI web en http://localhost:8025**
  (ahí ves los correos que manda la app en local).

```bash
docker compose down         # apagar la infra
```

---

## 6. Correr la aplicación

Todo se opera desde **`jornal`** (el "artisan" de milpa). Con `uv` antepón
`uv run python`; con el venv activo basta `./jornal`.

```bash
uv run python jornal serve            # API FastAPI (= artisan serve; --host --port --no-reload)
uv run python jornal queue work       # worker de Celery (tareas en background)
uv run python jornal schedule work    # beat: scheduler de crons (corre UNA sola instancia)
uv run python jornal schedule run     # despacha los crons del minuto (lo dispara el crontab del SO)
uv run python jornal list             # ve todos los comandos disponibles
```

`serve` arranca uvicorn con la app factory del kernel (`milpa.Core.Http.Http:create_app`);
por default escucha en `127.0.0.1:$APP_PORT` con `--reload`.

> **Beat: una sola instancia** (≈ `onOneServer()` de Laravel). Varios beats = crons
> duplicados. Los crons se declaran con `@cron_task(...)` (`src/milpa/Core/Cron`): gate por
> `APP_ENV` (`environments=[...]`), lock en Redis (`without_overlapping=True`) y logs
> por cron con rotación (`output="<nombre>"`).

### Frontend en dev (OPT-IN)

Si tienes `surcos/`, corre **en paralelo** a `jornal serve` el dev server del surco que estés
tocando:

```bash
uv run python jornal serve            # milpa sirve los shells (mismo origen)
pnpm --filter demo-spa dev            # dev server con HMR de UN surco
```

El dev server escribe el **hot-file** de su app (`surcos/<app>/hot`, con la URL del dev server);
el helper `vite()` lo detecta y emite el cliente HMR apuntando ahí — la página la sirve milpa, los
módulos los sirve Vite (el navegador habla con ambos). Cada surco tiene su hot-file, así un equipo
puede estar en dev con HMR mientras los demás corren su build, sin estorbarse. En **prod** no hay
hot-file: `pnpm -r build` deja cada surco en `public/<app>`, milpa lo monta en `VITE_ASSETS_URL` y
`vite()` emite los assets hasheados del manifest.

---

## 🎮 Demo corrible

Un demo completo (usuarios + notas) que ejercita TODO el stack: **auth dual** (JWT API + sesión
cookie/CSRF), **RBAC + ABAC**, **routing class-based** (`@Controller`/`@Get`), los **patrones
estilo milpa** (eventos→correos automáticos, mediator, pipeline, `@job`, `@cron_task`) y UI
**HTMX + Alpine + Pico.css**. Sobre **SQLite**, sin levantar infraestructura:

```bash
# 1) Config mínima en .env (sqlite + secretos)
echo 'DATABASE_URL=sqlite:///milpa.db'                  >> .env
echo 'JWT_SECRET=pon-un-secreto-largo-y-aleatorio'      >> .env
echo 'SESSION_SECRET=pon-otro-secreto-largo-aleatorio'  >> .env

# 2) migrar + sembrar + servir
uv run python jornal migrate run     # crea las tablas (Alembic, motor-agnóstico)
uv run python jornal db seed         # admin@demo.test + ana/beto + notas (todos: "password")
uv run python jornal serve           # http://127.0.0.1:8000
```

- **Web (HTMX):** abre `http://127.0.0.1:8000` y entra como `admin@demo.test` / `password`. Crea y
  borra notas (HTMX), y entra a **Usuarios** (solo rol `admin` → RBAC). Solo editas/borras tus
  propias notas (ABAC).
- **API (JWT):** `POST /api/login` → `{access_token}`; luego `Authorization: Bearer <token>` en
  `/api/me`, `/api/notes` (CRUD), `/api/admin/users`. OpenAPI en **`/docs`**.

El demo vive en `app/Modules/Demo/`; los modelos `User`/`Note` en `app/Models/`. Más en
[Autenticación](documentation/15-autenticacion.md).

### Microfrontends del demo (StackCraft)

El demo también trae dos `surcos/` que milpa sirve **en el mismo origen**, cada uno con su
controller:

- **`demo-spa`** (React 19 + react-router 7, con **file-router** por convención + **PWA**
  Serwist offline-first) → servido por `SpaController` en **`/spa`** (con catch-all SPA-fallback
  acotado al prefijo; `manifest.webmanifest` y `sw.js` como one-liners `Pwa.*`).
- **`tablero`** (vanilla JS, sin PWA) → servido por `TableroController` en **`/tablero`** — para
  mostrar que la convención del shell es del **framework**, no de la tecnología del frontend.

Con `pnpm install && pnpm -r build` (o `pnpm --filter demo-spa dev` para HMR) abres
`http://127.0.0.1:8000/spa` y `…/tablero`. **`milpa new <proj> --demo` materializa también el
frontend**: copia los surcos + el `package.json` raíz pnpm + `pnpm-workspace.yaml` + `.nvmrc` (los
PNG de la PWA viajan intactos), no solo el módulo Python.

---

## 7. Calidad (tests + guardrails)

Todo corre en local, **sin base de datos** (tests unitarios; sin TestContainers).

```bash
uv run pytest                       # tests (rápidos, sin BD)

uv run ruff check .                 # lint            | --fix  arregla
uv run ruff format .                # formato         | --check  solo verifica (CI)
uv run mypy                         # tipos (estricto)
uv run lint-imports                 # fronteras entre módulos
```

Todo de una (lo que validaría el CI):

```bash
uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run lint-imports && uv run pytest
```

> Un test solo: `uv run pytest Tests/Core/Mail/test_Mailer.py::test_x` · por palabra:
> `uv run pytest -k "mail"` · `-x` corta al primer fallo, `-v` verbose.

---

## 8. Estructura

```
src/milpa/           # EL PAQUETE importable (instalación local; ver §2)
  Core/              # EL FRAMEWORK (genérico, reutilizable):
    Config/          #   settings (pydantic-settings, lee .env)
    Console/         #   kernel de consola (Typer) + comandos + borde de error
    CeleryApp/       #   app de Celery + dispatch (broker-agnostic)
    Jobs/            #   @job (background on-demand) + .dispatch()
    Cron/            #   @cron_task + scheduler estilo Laravel
    Events/          #   Events/Observers (dispatch 1:N, broker-adaptive)
    Mediator/        #   command bus 1:1 (@handles / send)
    Pipeline/        #   pipeline modelo cebolla (estilo Laravel)
    Database/        #   Repository, @transactional, Filtering, mixins (engine agnóstico)
    Auth/            #   RBAC + ABAC (Gate/@policy), JWT + sesión, Passport
    Errors/          #   DomainError + RFC 9457 (problem+json)
    Http/            #   create_app() FastAPI + @Controller + RateLimit + middlewares
                     #   + Shell (runtime-config del shell: base_path/runtime_env_json/shell_context)
    Mail/            #   Mailable + Mailer (smtp/log/null) + TemplateEngine
    Translate/       #   i18n (i18nice, YAML)
    View/            #   templates (Jinja2) + negotiate() + Vite (helper vite()) + Pwa (manifest/SW)
  Models/            # modelos SQLAlchemy compartidos (auto-discovery)
  Dictionaries/      # constantes de dominio (auto-discovery por submódulo)
  Modules/
    Demo/            # módulo de referencia: users/notes + TODOS los patrones, ejecutable
  Resources/         # assets/lang/views compartidos
surcos/              # FRONTEND (OPT-IN): una app Vite por vertical (microfrontend) — surcos/<app>
public/              # builds de Vite (vite build de cada surco → public/<app>); GENERADO, gitignored
package.json         # raíz del workspace pnpm de los surcos (scripts dev/build)
pnpm-workspace.yaml  # workspaces pnpm (surcos/*): node_modules por paquete + allowBuilds
.nvmrc               # versión de Node para los frontends (22: pnpm 11 exige >=22.13)
Tests/               # tests unitarios (espeja src/milpa/ 1:1, sin BD)
migrations/          # revisiones Alembic (motor-agnóstico)
documentation/       # manual de usuario (mkdocs)
docs/                # ADRs y notas de diseño
secrets/             # llaves locales (contenido ignorado por git)
jornal               # entrypoint de consola (artisan) en la raíz
docker-compose.yml   # SOLO infra: redis + mailpit (+ rabbitmq opcional)
```

---

## 9. Arquitectura (de un vistazo)

Monolito **modular**: un **kernel compartido** (`Core`/`Models`/`Dictionaries`) y
**módulos independientes** (`app/Modules/*`) que **no se importan entre sí** (lo fuerza
`import-linter`). Cada módulo es un microservicio en potencia: se puede extraer sin
desenredar imports cruzados.

- **Persistencia estilo Spring Data.** `Repository[Model, Id]` tipado (CRUD heredado),
  escrituras en services `@transactional` (commit/rollback automático), lecturas con
  `@auto_session`. El engine es **agnóstico del motor** (se elige por `DATABASE_URL`);
  lo específico de cada dialecto está aislado en `Core/Database/Session.py`.
- **Tareas y crons.** Celery con transporte **agnóstico** (`BROKER_URL`): Redis o
  RabbitMQ en local, nubes como referencia. Los crons se declaran con `@cron_task`.
- **Correo.** `Mailable` + `Mailer` con drivers intercambiables (`smtp`/`log`/`null`),
  plantillas Jinja2 e i18n por YAML.
- **HTTP.** `create_app()` arma FastAPI, monta los módulos activos y fija el locale en
  el **boundary** (ambiente); middlewares (CORS/TrustedHost/GZip) con defaults seguros.
- **Calidad forzada.** Ruff + MyPy estricto + import-linter + pytest como guardrails.

---

## 10. Agregar un módulo

1. Crea `app/Modules/<Nombre>/` (mira `Modules/Demo` como referencia viva).
2. Pon dentro lo que necesite: `Http/` (rutas), `Services/`, `Repositories/`, `Jobs/` (@job),
   `Crons/` (@cron_task), `Observers/` (eventos), `Handlers/` (mediator), `Pipes/` (pipeline),
   `Policies/` (ABAC), `Mail/`, `Resources/` (lang/views namespaced), `Console/Commands/`.
3. Actívalo por configuración. La API y el beat lo **descubren solos**; el
   `import-linter` garantiza que no se enrede con otros módulos.

No tocas el kernel: el framework descubre modelos, diccionarios, recursos, comandos y
crons por convención.

**Si el módulo trae frontend:** agrega su app Vite como un surco (`surcos/<app>`, con su
`vite.config` usando `vite-plugin-milpa`) y, en el `Http/` del módulo, un controller que sirva el
shell Jinja con el helper `vite()` (más `shell_context(request)` para el `window.__ENV`). Es el
mismo patrón del Demo (`SpaController`/`TableroController`): el surco se auto-detecta por convención
y milpa lo sirve en `<VITE_ASSETS_URL>/<app>` — mismo origen, cero CORS.

---

## Notas

- **Borrado lógico** (`deleted_at`) y **timestamps** (`created_at`/`updated_at`) son
  automáticos y declarativos (estilo Laravel/JPA); las fechas usan la zona de `TIMEZONE`.
- **Auto-discovery**: soltar un modelo en `app/Models`, un diccionario en
  `app/Dictionaries` o un módulo en `app/Modules` "simplemente funciona", sin editar
  índices a mano.
- **Migrar desde Laravel**: el kernel reproduce conceptos familiares (artisan→`jornal`,
  scheduler→`@cron_task`, mailables, soft-deletes, timestamps, validación de tokens
  Passport) para acortar la curva.
