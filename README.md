# auth-service-fastapi

#### A production-oriented Authentication Microservice built with FastAPI, SQLAlchemy 2.0, and Redis.

![python](https://img.shields.io/badge/python-3.12-blue)
![fastapi](https://img.shields.io/badge/fastapi-0.135-green)
![license](https://img.shields.io/badge/license-MIT-brightgreen)

[Project Setup](#project-setup) • [Endpoints](#endpoints) • [System Design](#system-design) • [Architecture](#architecture) • [Token Security](#token-security) • [Environment Variables](#environment-variables) • [Future Improvements](#future-improvements)

---

## Project Setup

### User Setup

```bash
docker compose -f docker-compose-dev.yml up -d
```

### Developer Setup

1 — I'm using [uv](https://docs.astral.sh/uv/) as package manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2 — Install dependencies

```bash
uv sync
```

3 — Add your secrets to `.env` file

```bash
cp .env.example .env
```

4 — Start the infrastructure (PostgreSQL + Redis + pgAdmin)

```bash
docker compose -f src/docker-compose-dev.yml up -d
```

5 — Run the server

```bash
uv run python main.py
```

6 — Run the tests

```bash
uv run pytest
```

7 — API docs

```
http://localhost:8000/docs
```

---

## Endpoints

- `/docs/` : interactive Swagger UI

**Users**

- `/users/` :
  - `POST` — register a new user (creates user + profile atomically)
  - `PUT` — update user fields (name, family, username)
  - `GET` — list all users with filters and pagination
- `/me/` :
  - `GET` — get the current authenticated user with profile
- `/users-profile/` :
  - `GET` — list users joined with their profiles

**Auth**

- `/auth/login` :
  - `POST` — authenticate with username + password, returns access + refresh token pair
- `/auth/refresh` :
  - `POST` — issue a new access token using a valid refresh token
- `/auth/logout` :
  - `POST` — revoke both tokens (DB revocation + Redis blacklist)
- `/auth/register-access` :
  - `POST` — validate an access token and return its payload
- `/auth/register-refresh` :
  - `POST` — validate a refresh token and return payload + family_id

---

## System Design

### Request Lifecycle

Every authenticated request passes through two validation layers before reaching a route:

1. The access token JTI is checked against the **Redis blacklist** (fast O(1) lookup).
2. The token signature and claims (`exp`, `iss`, `aud`, `nbf`) are verified by **python-jose**.

This means even a structurally valid token is rejected instantly after logout, without touching PostgreSQL.

### Session Lifecycle

Sessions are **not** injected via FastAPI `Depends` at the route level. Controllers open `async with session_factory()` explicitly and release the connection immediately after the DB step.

This prevents `idle_in_transaction` — a common production failure where connections stay open while the application does non-DB work (hashing, HTTP calls, cache writes), exhausting the connection pool under load.

### Infrastructure

```
Client
  │
  ▼
FastAPI (Uvicorn)
  │
  ├── PostgreSQL 16 (asyncpg + SQLAlchemy 2.0)
  │     └── users, profiles, refresh_tokens
  │
  └── Redis 8 (async)
        └── access token blacklist
            refresh token blacklist (on logout)
```

---

## Architecture

This project follows a strict **layered architecture**. Dependencies only flow downward — routers know nothing about repositories, and repositories know nothing about JWT.

```
src/
├── main.py
├── auth/
│   ├── controller.py          — orchestrates login / refresh / logout
│   ├── routers.py
│   ├── repository.py
│   ├── dependencies.py
│   ├── schamas.py
│   └── expections.py
├── users/
│   ├── controllers.py         — orchestrates registration flow
│   ├── router.py
│   ├── service.py
│   ├── selectors.py           — all read queries
│   ├── repository.py
│   ├── dependencies.py
│   ├── schemas.py
│   └── exceptions.py
├── models/
│   ├── user.py                — User + Profile ORM models
│   ├── tokens.py              — RefreshTokenModel + ApiToken
│   └── enums.py
├── core/
│   ├── config.py              — settings via pydantic-settings
│   ├── base/
│   │   ├── repository.py      — Generic BaseRepository[T]
│   │   └── services.py        — BaseAbstractService (3-phase pattern)
│   └── security/
│       ├── jwt/               — TokenService + JWTController
│       ├── refresh_tokens/    — RefreshTokenStoreRepository
│       └── utils/             — hashing + token generation
├── infrastructure/
│   ├── sqlalchemy/            — AsyncSession, engine, declarative base
│   └── redis/                 — RedisManager + connection pool
└── test/
    ├── unit/
    ├── integration/
    ├── e2e/
    ├── fixtures/
    └── factories/
```

### Three-phase Service Pattern

`BaseAbstractService` enforces a deliberate execution order to keep transactions tight:

- **Pre-process** — CPU-bound work outside the transaction (password hashing, token generation, input normalization)
- **DB-process** — only database writes inside `async with session.begin()`, no external awaits
- **After-process** — post-commit side effects (cache writes, event publishing, emails)

### Key Patterns

- **Repository Pattern** — `BaseRepository[T]` is generic, providing `find`, `create`, `update`, `delete`, `exists`, and `filter_by_*` methods reused across all domain repositories.
- **Dependency Injection** — services, repositories, and infrastructure clients are injected at the controller level, keeping layers testable in isolation.
- **Async-first** — all DB and cache operations are fully async via `asyncpg` and `aioredis`.

---

## Token Security

### Token Types

| Token | TTL | Storage | Revocation |
|-------|-----|---------|------------|
| Access | `ACCESS_TOKEN_EXPIRE_MINUTES` (default 900) | Client-side only | Redis blacklist on logout |
| Refresh | `REFRESH_TOKEN_EXPIRE_DAYS` (default 43200) | PostgreSQL `refresh_tokens` table | DB `revoked_at` + Redis blacklist |

### Token Claims

```json
{
  "sub":  "user_id",
  "jti":  "unique-token-id",
  "type": "access | refresh",
  "iat":  1234567890,
  "nbf":  1234567890,
  "exp":  1234567890,
  "iss":  "configured-issuer",
  "aud":  "Auth_service"
}
```

### Token Family and Reuse Detection

Each login creates a `family_id` derived from the user-agent and IP hash. All refresh tokens in a session share this `family_id`. The `RefreshTokenStoreRepository` exposes `revoke_family()` to invalidate an entire session on detected reuse.

The `rotated_from` field on each refresh token stores the `jti` of the token it replaced, giving a full rotation lineage for audit.

### Logout Flow

1. Verify both tokens are structurally valid.
2. Mark the refresh token as `used` and `revoked` in the DB (single transaction).
3. Blacklist the refresh token `jti` in Redis with TTL = remaining token lifetime.
4. Blacklist the access token `jti` in Redis with TTL = 5 minutes.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | required | PostgreSQL DSN — `asyncpg` driver enforced automatically |
| `REDIS_URL` | required | Redis connection URL |
| `SECRET_KEY` | required | JWT signing secret |
| `JWT_ALGORITHM` | required | e.g. `HS256` |
| `ISSUER` | required | JWT `iss` claim value |
| `AUDIENCE` | `Auth_service` | JWT `aud` claim value |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `900` | Access token TTL in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `43200` | Refresh token TTL in days |
| `ENVIRONMENT` | required | `development` or `production` |
| `HOST` | `localhost` | Uvicorn bind host |
| `POST` | `8000` | Uvicorn bind port |
| `SQL_ECHO` | `False` | Log all SQL statements (dev only) |

---

## Libraries

- [FastAPI](https://fastapi.tiangolo.com/) — async web framework
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) — async ORM with `asyncpg` driver
- [python-jose](https://python-jose.readthedocs.io/) — JWT signing and verification
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — environment config
- [Redis (aioredis)](https://redis.io/) — token blacklist
- [pytest](https://docs.pytest.org/) — testing framework
- [uv](https://docs.astral.sh/uv/) — package manager

---

## Future Improvements

1. **Wire `/me` route** — the current-user JWT dependency exists but is not yet connected; `cur_user` is hardcoded to `1`.

2. **Tests** — the structure is fully scaffolded (`unit/`, `integration/`, `e2e/`, `fixtures/`, `factories/`) but all files are empty. Integration tests for login, refresh, and logout are the critical path.

3. **Email verification flow** — the `token_hash` field and hashing utilities are in place; the verification endpoint and email dispatch are not yet implemented.

4. **Redis caching for users** — post-registration cache population is noted as a TODO in `UserRegistrationController`.

5. **Alembic migrations** — schema is currently created via `Base.metadata.create_all`; proper migration management is needed before production deployment.

6. **Logging** — `print()` debug statements are scattered through service and controller layers and need to be replaced with structured logging.

7. **Bulk user creation** — endpoint code is scaffolded but commented out.
