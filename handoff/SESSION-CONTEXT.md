# Capture IV: context for the next Claude session

Read this first. It carries over what the previous Claude Code session (Nov 3–4, 2026)
did, what is still open, and the owner's rules. No secrets are in this file.

## Repositories
- **`filpl/captureiv`** (production). Render deploys `main` to `app.captureiv.com`. `main` was at `24a63da` when this was written.
- **`filpl/captureiv-2`** (redesign work). This file lives on branch `claude/captureiv-handoff-audit-ibu3wu`, next to `handoff/README.md`, the git bundles, the patch files and `issues-for-separate-fixes.md`.

## Open pull requests on `filpl/captureiv` (none merged)
Merge in this order, and **only after the owner says to**. Each merge deploys production.

| PR | Branch | What it does |
|---|---|---|
| #13 | `feature/viewer-security-step1` | Clients need the share link **and** the 4-letter code. Each link locks for 1 hour after 10 wrong codes. Viewer sessions expire after 12 h. Adds security headers. |
| #14 | `feature/legal-pages` | `/legal` pages, consent on sign-up and invites, and an indented, boxed Terms Section 9 (arbitration and class-action waiver, 30-day opt-out). Shows a draft banner until `LEGAL_TERMS_APPROVED=1`. **The owner needs a lawyer's review before approving.** |
| #15 | `feature/viewer-layout` | New angular-C logo across the app, and the redesigned client viewer. The top Share button is **kept** (owner approved). Its note now reads: "Share both the link and the code only with people on your project team. Anyone with both can view this project." (commit `2e241af`). |
| #16 | `feature/worker-accounts` | Workers add flight days, routes and route videos, and upload or edit documents, on assigned projects only. Admins and workers share one Workspace (Videos & routes + Documents); admins keep their oversight tools. Fixes a live bug: worker uploads saved nothing (StorageReservation tenant scope). |

`preview/all-changes` (local only in the old session) combined all four branches. Its merge conflicts were resolved in `access.html`, `employee_setup.html`, `project_view.html` and `site_capture.html`.

**Tests:** every module matches `main` except for 22 new tests, which pass. Two failures already existed on `main` and are unrelated: `test_launch_diagnostics`, and the rate-limit pruning test in `test_saas_isolation.py`.

## After each merge: checks to run with the owner
1. `https://app.captureiv.com/api/health` returns `{"status":"ok"}`.
2. The project map loads, with no Google Maps key errors in the console.
3. In a private window: the share link + code opens the viewer, and the code alone on the home page does not.
4. Worker: on an assigned project, add a route with a throwaway video and upload a throwaway document. Both should save, and an unassigned project should not be visible.
5. Stripe: test only on a staging service with **test** keys.

Optional Render settings: `LEGAL_ENTITY_NAME`, `LEGAL_POSTAL_ADDRESS`, `LEGAL_GOVERNING_LAW`, `LEGAL_ARBITRATION_PROVIDER`, `LEGAL_ARBITRATION_LOCATION`. Set `LEGAL_TERMS_APPROVED=1` only after legal review.

## Owner's rules (do not break these)
- **Pushing, merging and deploying:**
  - Don't push, merge or deploy without the owner's explicit OK.
  - Never force-push.
  - Never deploy a different repo by assumption.
- **Secrets:** never print, paste or commit them (Stripe keys or webhook secret, R2 credentials, database URL, SMTP, Maps key).
- **Stripe:** no live charges without explicit approval; use test mode or staging.
- **Weekly job:** don't trigger `captureiv-weekly-project-codes` by hand.
- **Approvals needed:** emails to customers, permission changes, production cutover and destructive operations.
- **Customer data:** don't remove or replace it, and keep the R2 bucket private.
- **Marketing site:** `captureiv.com` stays private; it's not approved for public launch.
- **Naming:** never show "HERSHEY CAPITAL LLC" publicly.
- **DMCA:** the DMCA agent isn't registered, so don't claim it is.
- **Sandbox:** hidden from company and client accounts (owner only).
- **Branches:** keep security fixes separate from redesign branches.

## Open decisions and reminders
- Should a worker invite be part of company sign-up?
- Should Photos come back for admins in the Workspace?
- Lawyer review of the terms: a reminder was set for Nov 6.
- Later: port the website redesign (`capture-iv-website-redesign` in `filpl/captureiv-2`) into the production `landing-page/`. The site stays private.

## Redesign branches in `filpl/captureiv-2`
- `capture-iv-website-redesign`: the website, with dark-band option B and the centred C logo.
- `user-platform-ui-redesign`: the platform UI, with Sandbox owner-only and the footer-only viewer logo.
- Save-point tags `savepoint-2026-11-03-website` and `savepoint-2026-11-03-platform` are in `handoff/captureiv-2/redesign-branches.bundle`.

## Running production locally
1. Use Python 3 and `pip install -r requirements.txt`.
2. Set `DATABASE_URL=sqlite:///local.db` and `SECRET_KEY=<any local value>`.
3. Run `python app.py`.
4. Run tests one module at a time: `python -m pytest -q tests/test_<name>.py`.
