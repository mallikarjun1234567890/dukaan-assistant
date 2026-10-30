# Dukaan Assistant

Hackathon MVP for small retail shops: inventory, invoices, reorder recommendations, and a Gemini-powered shop assistant.

This is a working single-shop demo, not a production SaaS. Shop-owned tables already include `shop_id` so multi-tenant isolation can be added later without redesigning the core schema.

## Architecture

- React + Vite frontend on `http://localhost:5173`
- FastAPI backend on `http://localhost:8000`
- Postgres via SQLAlchemy (one shop database)
- HttpOnly JWT cookie + readable CSRF cookie
- AI is called only from the backend, with a Python-built shop snapshot
- Fallback order: Gemini → Groq → hosted Hugging Face → local Ollama (`llama3.2`)

```
Browser  →  Vite React app  →  FastAPI  →  Postgres
                              └── Gemini → Groq → Hugging Face → Ollama
```

## Tech stack

**Frontend:** React, Vite, TypeScript, Tailwind CSS, Lucide React, Recharts

**Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, Postgres, Pydantic, PyJWT, pwdlib/Argon2, Google GenAI / Groq / Hugging Face / Ollama, Cloudinary, Razorpay (test)

## Folder structure

```
frontend/          React app
backend/app/       FastAPI application
backend/tests/     Isolated pytest suite
backend/data/      unused leftover folder (gitignored)
```

## Prerequisites

- Python 3.11 or newer (`python` or `py` on Windows)
- Node.js 20+ and npm
- A Gemini API key only if you want Ask Dukaan AI to answer (Groq, Hugging Face, or local Ollama are optional backups)
- Cloudinary credentials only if you want product/shop/profile photos
- Razorpay **test** keys only if you want the ₹1 checkout demo
- Postgres running locally (or via Docker). Set `DATABASE_URL` in `backend/.env`

## Local development (Windows PowerShell)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set a long random `JWT_SECRET` (32+ characters). Leave `GEMINI_API_KEY` empty if you do not have a key.

Generate a secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Initialize the database and demo account (safe to re-run; it does not wipe existing users):

```powershell
python -m app.seed
```

Start the API:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

- API health: http://localhost:8000/api/health
- Swagger: http://localhost:8000/docs

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

App URL: http://localhost:5173

## Demo account

Created by `python -m app.seed`:

- Email: `owner@dukaan.local`
- Password: `Demo@12345`
- Shop: Sharma Kirana Store

The seed also adds realistic grocery and stationery products, including low-stock items such as Fortune cooking oil and Amul milk.

## Ask Dukaan AI configuration

Python still owns stock, sales, and shop time. The model only explains that snapshot.

Fallback order if a provider is missing or fails:

1. Gemini (`GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`)
2. Groq (`GROQ_API_KEY`)
3. Hosted Hugging Face (`HF_TOKEN`)
4. Local Ollama (`OLLAMA_BASE_URL=http://127.0.0.1:11434`, `OLLAMA_MODEL=llama3.2`)

Never put keys in `VITE_` frontend variables. If every provider is missing, inventory, invoices, dashboard, and reorders still work.

## Cloudinary photos

Optional. Add `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` to `backend/.env`, then upload a shop logo, profile photo, or product image from the UI. Secrets stay on the backend.

## Postgres

The running app uses **one** database: Postgres. Put this in `backend/.env` (adjust user/password/host if yours differ):

```
DATABASE_URL=postgresql+psycopg://dukaan:dukaan@localhost:5432/dukaan
```

If you already have a `postgresql+pg8000://...` URL, keep it. Do not point the app at a SQLite file.

## Razorpay test checkout

Optional and test-mode only. Add `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` from a Razorpay test account. Shop hours, inventory, and invoices work without it. A successful ₹1 test payment only marks the shop plan as `test`.

## Demo workflow

1. Open http://localhost:5173 and sign in.
2. Review dashboard cards (live Postgres totals).
3. Add a product on Inventory.
4. Open a low-stock product (for example Fortune Sunflower Oil).
5. Approve its recommendation on Reorder Recommendations.
6. Create an invoice for an in-stock product.
7. Confirm stock dropped once, then check dashboard sales.
8. Ask Dukaan AI: "Which products need restocking today?"

## Business rules

- Money is stored as integer paise. API responses also include rupees.
- Invoice totals are calculated only on the backend.
- Confirmed invoices deduct stock in one transaction. Failure rolls everything back.
- Duplicate submissions reuse the client `idempotency_key` and do not deduct stock twice.
- Invoice item names and unit prices are snapshots. Later product edits do not rewrite history.
- Sales totals include only `confirmed` invoices. Cancelled invoices are excluded. Refunds are not implemented.
- Reorder quantity = `max(0, (2 × minimum stock) − current stock)`.
- Approving a reorder only stores an internal request. It does not contact a supplier or take payment.

## Security decisions and limitations

Implemented:

- Argon2 password hashes
- Short-lived JWT in an HttpOnly `SameSite=Lax` cookie
- Double-submit CSRF cookie + `X-CSRF-Token` header on cookie-authenticated mutations
- Bearer tokens accepted for tests and API clients (no CSRF when the cookie is absent)
- Shop-scoped queries; client-supplied shop IDs are not trusted
- CORS allow-list of exact origins
- Request size limit, AI rate limit, provider timeouts
- Secrets required from environment; server refuses to start without a strong `JWT_SECRET`
- AI replies rendered as text, not HTML

Documented trade-offs:

- This is a hackathon MVP, not production-secure SaaS.
- Tokens live in cookies, not `localStorage`. SessionStorage is also unused.
- CSRF protects cookie-authenticated writes. Login itself does not require CSRF.
- Back up Postgres with `pg_dump`. Do not keep a second SQLite copy of shop data.
- Use HTTPS in any deployment and set `COOKIE_SECURE=true`.
- No password reset, 2FA, audit log, or tenant admin console.
- In-memory AI rate limits reset when the process restarts.
- Gemini sees a minimized shop snapshot. Do not paste unrelated personal data into chat.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `JWT_SECRET is missing or too weak` | Put a 32+ character secret in `backend/.env` |
| Login fails after seed | Confirm `DATABASE_URL` in `backend/.env` points at the same Postgres the API uses |
| Frontend cannot call API | Backend on port 8000, `VITE_API_BASE_URL=http://localhost:8000`, CORS origin `http://localhost:5173` |
| 403 CSRF error | Reload after login so the CSRF cookie is present |
| AI returns 503 | No provider key, or Gemini / Groq / Hugging Face / Ollama all failed |
| PowerShell blocks venv activation | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Tests use a throwaway empty file so they never read or write your Postgres shops.

Frontend production build:

```powershell
cd frontend
npm run build
```

## Optional Docker

Local `python` / `npm` commands above are enough. Docker is optional.

Create a compose env file (do not commit it):

```powershell
$env:JWT_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")
```

Or a root `.env` containing `JWT_SECRET=` and optional `GEMINI_API_KEY=`.

```powershell
docker compose up --build
```

Then seed the persisted volume once:

```powershell
docker compose exec backend python -m app.seed
```

- App: http://localhost:8080
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

Stop with `docker compose down`. Logs: `docker compose logs -f backend`. Shop data lives in the `dukaan-pg` Postgres volume.

Never bake secrets into images. Compose reads `JWT_SECRET` from the environment.

## Production gaps

- Multi-user shops, invites, and role permissions
- HTTPS termination, hardened cookie flags, and a real CSRF origin check
- Managed Postgres backups and a proper migration tool (Alembic)
- Invoice taxes, GST, refunds, and payment collection
- Supplier purchase orders
- Observability, abuse controls, and a proper AI data-retention policy
