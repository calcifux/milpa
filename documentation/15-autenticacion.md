# Autenticación

milpa trae validación de **tokens OAuth2 de Laravel Passport** (JWT RS256) lista para
usar, en `app/Core/Auth`. Es el caso típico al migrar un backend desde Laravel: el
emisor de tokens sigue siendo el sistema legacy (o un servicio de auth aparte) y milpa
solo **valida** los tokens con la llave pública.

> milpa **valida** tokens; no los **emite**. El login / emisión vive en tu proveedor
> de OAuth2 (Passport).

## Configuración

Copia la llave **pública** RS256 de Passport (en el legacy:
`storage/oauth-public.key`) a `secrets/` y apunta el `.env`:

```bash
PASSPORT_PUBLIC_KEY_PATH=/secrets/oauth-public.key
# PASSPORT_PUBLIC_KEY=          # alternativa: la llave en texto, en vez de la ruta
# PASSPORT_EXPECTED_AUDIENCE=   # opcional: valida el claim "aud"
```

Ver [Configuración](03-configuracion.md) y la sección de [secrets](02-instalacion.md).

## Proteger una ruta

`app/Core/Auth` expone dependencies de FastAPI:

```python
from fastapi import APIRouter, Depends
from app.Core.Auth import get_current_token, require_scopes, TokenPrincipal

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/profile")
def profile(principal: TokenPrincipal = Depends(get_current_token)) -> dict:
    return {"user_id": principal.user_id, "scopes": principal.scopes}

@router.post("/admin")
def admin(principal: TokenPrincipal = Depends(require_scopes("admin", "write"))) -> dict:
    return {"user_id": principal.user_id}
```

### `get_current_token`

Dependency que extrae el `Authorization: Bearer <jwt>`, lo decodifica con la llave
pública (RS256), verifica el `aud` si configuraste `PASSPORT_EXPECTED_AUDIENCE`, checa
revocación, y devuelve un `TokenPrincipal`.

### `require_scopes(*scopes)`

Factory de dependency: encadena a `get_current_token` y además exige que el token tenga
todos los scopes indicados. Si falta alguno → `403`.

### `TokenPrincipal`

```python
@dataclass
class TokenPrincipal:
    user_id: str | None      # claim "sub"
    client_id: str | None    # claim "aud"
    token_id: str | None     # claim "jti"
    scopes: list[str]        # claim "scopes"
```

## Respuestas de error

| Situación | Código |
|-----------|--------|
| No hay llave pública configurada | `503` (problema de **infraestructura**, no de auth) |
| Token inválido / expirado / firma mala | `401` |
| Token válido pero faltan scopes | `403` |

> La distinción `503` vs `401` es a propósito: sin llave configurada es un fallo de
> despliegue (te falta el secret), no que el cliente mandó un token malo.

## Alternativa: seguridad propia del módulo

Si no usas Passport, puedes proteger un router con tu propia dependency (ej. una API
key), sin tocar el kernel. Ver el patrón en
[Rutas y controladores](07-rutas-y-controladores.md#proteger-rutas).

## Nota sobre revocación

La verificación de revocación está preparada como punto de extensión (consultar la tabla
de tokens del legacy). Hoy no bloquea por revocación; valida firma, expiración y
audiencia. Revísalo si tu modelo de amenazas exige revocación inmediata.

## Siguiente paso

[Base de datos](16-base-de-datos.md).
