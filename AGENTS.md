# AGENTS – Production Repo (TradingAgents-Production-Complete)

## Purpose
Authoritative notes for CI/CD, environments, and secrets used by this repo.

## Environments
- Firebase project: `tradingagents-main` (aka TradingAgents Main)
- Hosting targets:
  - `main-site` → 03king (primary site)
  - `admin` → admin-03king (admin site)
- Backend/CORS: allow `https://03king.com` and `https://admin.03king.com`.

## GitHub Actions secrets (in THIS repo)
- `FIREBASE_PROJECT_ID` = `tradingagents-main` (optional; workflow defaults if empty)
- Credentials – provide ONE of:
  - `FIREBASE_SERVICE_ACCOUNT` = Admin SDK JSON for `tradingagents-main`
  - or `FIREBASE_TOKEN` = `firebase login:ci` token
- Supported alias for service account JSON: `TRADINGAGENTS_MAIN`

## Workflows
- `.github/workflows/frontend-prod-ci.yml`
  - Build + preview on port 3000 (Vite preview), optional Playwright smoke
  - Deploy when `deploy=true`
  - Auto-detect `build/` or `dist/` output
  - Uses `FIREBASE_SERVICE_ACCOUNT` or `TRADINGAGENTS_MAIN`, or `FIREBASE_TOKEN`
  - Diagnostics included:
    - `firebase target:display hosting --config firebase.json`
    - `firebase target:display hosting --config firebase.admin.json`
    - `firebase projects:list --json`

## CORS validation (backend)
Backend must only allow:
- `https://03king.com`
- `https://admin.03king.com`

FastAPI example (app.py):
```
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "https://03king.com",
    "https://admin.03king.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Runtime check (replace API_HOST):
```
curl -I -H "Origin: https://03king.com" https://API_HOST/health | grep -i access-control-allow-origin
curl -I -H "Origin: https://admin.03king.com" https://API_HOST/health | grep -i access-control-allow-origin
```
回傳的 `Access-Control-Allow-Origin` 應分別等於你的測試 Origin；對未允許的來源則不應回傳此標頭。

## Rollback (Firebase Hosting)
- 查看 releases：`firebase hosting:releases --project tradingagents-main --site 03king`
- 回滾主站：`firebase hosting:rollback --project tradingagents-main --site 03king <releaseId>`
- 回滾後台：`firebase hosting:rollback --project tradingagents-main --site admin-03king <releaseId>`

## Security
- Never commit secrets. Rotate any leaked keys in GCP → Service Accounts.
- Admin production CSP forbids localhost/echo test endpoints.
