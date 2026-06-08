---
paths:
  - "app/**/api/*.py"
  - "app/**/public_api/*.py"
  - "app/common/api/rate_limit.py"
---

# Rate Limiting

Redis-backed rate-limit dependencies live in `app/common/api/rate_limit.py`. Pick the helper
that matches who you are throttling and whether failed attempts should count.

## The three patterns

| Helper | Keyed on | Counts failures? | Use for |
|--------|----------|------------------|---------|
| `rate_limit(prefix, ttl)` + `confirm_rate_limit(request)` | authenticated user | no (only on success) | expensive authenticated actions that must not be re-triggered |
| `rate_limit_by_ip(prefix, window, max_attempts)` | client IP | yes (every attempt) | anonymous auth routes (login) to defeat brute force |
| `public_api_rate_limit` | organization | yes (every request) | the per-org public API |

## Per-user, success-only — `rate_limit` + `confirm_rate_limit`

`rate_limit` rejects with HTTP429 if the user is already limited, but does **not** set the key.
Call `confirm_rate_limit(request)` at the end of the handler, after the work succeeds, so a
failed request (e.g. a 409 duplicate) does not consume the user's quota. It reads
`request.state.user`, so `auth_user` must already be applied.

```python
@router.post('', dependencies=[Depends(rate_limit('create-example-resource', ttl_seconds=60))])
def create_resource(request: Request, body: ExampleResourceCreate, db: DBSession = Depends(get_db)):
    resource = db.create(ExampleResource(**body.model_dump(), organization_id=request.state.user.organization_id))
    confirm_rate_limit(request)
    return resource
```

## Per-IP, count-every-attempt — `rate_limit_by_ip`

For anonymous endpoints, throttle even failed attempts so credential stuffing is bounded.
`INCR` + an idempotent `EXPIRE ... NX` make the counter atomic and crash-safe (a worker
crash between INCR and EXPIRE can't leave a TTL-less, permanently-throttling key).

```python
@anon_router.post('/auth/login', name='login', dependencies=[Depends(rate_limit_by_ip('login', 60, 5))])
def login(body: UserLogin, session: DBSession = Depends(get_db)) -> Token:
    ...
```

`get_client_ip(request)` reads the **rightmost** `X-Forwarded-For` entry, which is only safe
behind a trusted proxy that appends the real client IP. Without such a proxy, an attacker can
spoof XFF — gate it on a trusted-proxy allowlist before relying on it for security.

## Per-organization — `public_api_rate_limit`

A fixed-window Redis counter (`rate_limit:public_api:{organization_id}`, INCR +
`EXPIRE ... NX`) caps each org at `settings.public_api_rate_limit_per_minute` (default 600)
over `settings.public_api_rate_limit_window_seconds` (default 60); over-limit → HTTP429. Wire
it as a router-level dependency **after** `api_key_auth`, so `request.state.organization_id`
is set.

Key on the **organization, not the API key**, so minting more keys (cap: 10) can't multiply
the quota. A reverse proxy / CDN can only limit per IP, which is wrong here — one org may call
from many IPs (or several orgs may share one via NAT) — hence the app-level limit.

```python
public_router = APIRouter(
    prefix='/example-resources',
    dependencies=[Depends(api_key_auth), Depends(public_api_rate_limit)],
)
```
