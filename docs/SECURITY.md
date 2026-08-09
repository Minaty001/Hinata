# Hinata — Security Guide

---

## Secrets Management

Hinata uses environment variables for all secrets. The `.env` file (never committed) holds
local development values. Production deployments use CI/CD environment variables or a secrets manager.

### Required Secrets

| Variable | Purpose | How to Generate |
|----------|---------|----------------|
| `JWT_SECRET` | Signs JWT access/refresh tokens | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `BOT_TOKEN` | Telegram bot token | Request from [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | Groq AI provider | [console.groq.com](https://console.groq.com) |

### Optional AI Provider Keys

Set only the providers you use. The system falls back automatically:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENCODE_ZEN_API_KEY`
- `BYTEZ_API_KEY`

### Android Signing (CI/CD Only)

**Never commit keystores or passwords to source control.**

Set these as secrets in your CI/CD pipeline (GitHub Actions → Settings → Secrets):

```
KEYSTORE_PATH      — absolute path to your .jks keystore (on the CI runner)
KEYSTORE_PASSWORD  — keystore password
KEY_ALIAS          — key alias
KEY_PASSWORD       — key password
```

---

## Generating a New Android Keystore

The original `hinata-keystore.jks` was exposed publicly and **must be considered compromised**.
Generate a new keystore before making any release builds:

```bash
keytool -genkey -v \
  -keystore hinata.jks \
  -alias hinata \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -storepass "$(python -c 'import secrets; print(secrets.token_urlsafe(24))')" \
  -keypass  "$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
```

Store the generated keystore in a **secure location outside the repository** (e.g., a password
manager, CI/CD secrets, or a hardware security module). Record the passwords securely.

---

## CORS Configuration

Set `WEB_ORIGINS` to the exact origins that should be allowed to call the API:

```env
# Development
WEB_ORIGINS=http://localhost:2027,http://127.0.0.1:2027

# Production
WEB_ORIGINS=https://your-hinata-domain.com
```

Wildcard (`*`) is **intentionally not supported** in production.

---

## API Authentication

From Phase 1 onwards, all API endpoints require a Bearer token:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via `POST /api/v1/auth/login` and refreshed via `POST /api/v1/auth/refresh`.

WebSocket connections authenticate via a token query parameter:
```
ws://server/api/v1/ws?token=<access_token>
```

---

## Provider API Key Security

- API keys are **never returned** in API responses (only the last 4 characters as a hint)
- API keys stored in the database are intended to be moved to server-side secrets in Phase 1
- The `/api/provider` endpoint (legacy) will require authentication in Phase 1

---

## Known Compromised Credentials

If you forked or cloned this repository before 2026-08-09, the following were exposed:

| Credential | Value | Action Required |
|-----------|-------|----------------|
| Android keystore | `flutter_app/android/keystore/hinata-keystore.jks` | Generate a new keystore |
| Keystore password | `hinata123` | Rotate immediately |
| Key alias | `hinata` | Use a new alias with new keystore |

---

## Reporting Security Issues

Please report security vulnerabilities privately. Do not open public GitHub issues for security bugs.
Contact the repository owner directly.
