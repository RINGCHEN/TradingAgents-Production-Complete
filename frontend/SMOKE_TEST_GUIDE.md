# Admin UI Smoke Test Guide (Phase 2)

This guide explains how to run the Phase 2 admin UI smoke tests using the MSW-backed mock API layer.

## Prerequisites

- Phase 1 branch `feature/admin-baseline` (or later) checked out
- Node.js ≥ 18 and npm installed
- MSW assets initialised (already committed in the repo)

## 1. Install Dependencies

From `TradingAgents-Production-Complete/frontend` run:

```bash
npm install
```

## 2. Start the Dev Server with MSW

```bash
npm run dev
```

`src/main.tsx` automatically boots the MSW browser worker in development. You should see the console log:

```
[MSW] Browser worker started (dev mode)
```

If the worker fails to start, a warning is printed but the app still mounts. Investigate the warning before continuing.

## 3. Navigate to the Admin UI

Open the dev server URL (default `http://localhost:5173`) and focus on `/admin/users`. Confirm that:

- The network tab shows requests being intercepted by MSW.
- No real backend calls are made.
- The user list shows the seeded mock data.

## 4. Execute Smoke Test Scenarios

Work through the scenarios defined in `PHASE_2_PREP.md`, Section 1. Recommended order:

1. **List Load & Pagination** – step through pages, adjust page size.
2. **Search & Filtering** – exercise `keyword` search and status filters.
3. **CRUD Happy Paths** – create, view, update, and delete a user.
4. **CRUD Error Paths** – use the devtools console to override MSW handlers and simulate failures.
5. **Data Integrity Checks** – verify camelCase ↔ snake_case mappings, role badge, timestamp warnings.

Record findings in the sprint QA log or the appropriate Jira ticket.

## 5. Reset Mock Data (Optional)

MSW handlers automatically reset between test runs, but you can reload the page to rehydrate the initial fixtures. For automated tests the jest hooks call `resetMockUsers()` after each spec.

## 6. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| `[MSW] Failed to start browser worker` | Service worker registration blocked | Ensure the page is served over `http://localhost`, not a `file://` URL. |
| Real network requests appear | MSW worker not registered | Reload the page; confirm the console log shows worker startup. |
| Stale mock data | Browser cache | Hard-refresh or clear site data. |
| React warnings about missing root element | `index.html` template missing `#root` | Re-run `npm install` to ensure Vite assets are intact. |

## References

- `frontend/src/mocks/handlers/adminUsers.ts` – mock backend contract
- `frontend/PHASE_2_PREP.md` – detailed scenario matrix
- `frontend/KNOWN_ISSUES.md` – outstanding tech debt tracked for later phases
