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

## Security
- Never commit secrets. Rotate any leaked keys in GCP → Service Accounts.
- Admin production CSP forbids localhost/echo test endpoints.

