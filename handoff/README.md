# Capture IV handoff (Nov 3–4, 2026)

Everything built in the Claude Code session, ready to apply. **Nothing here is merged or
deployed.** Your live site (`app.captureiv.com`, `filpl/captureiv` `main` at `24a63da`) is
unchanged until you merge.

## What's here

| Path | What it is |
|---|---|
| `captureiv-production/captureiv-changes.bundle` | Git bundle with the 5 new branches for **`filpl/captureiv`** (needs `main` at `24a63da`) |
| `captureiv-production/patches/<branch>/` | The same work as patch files, one folder per branch |
| `captureiv-2/redesign-branches.bundle` | The earlier redesign branches in **`filpl/captureiv-2`**, plus the Nov 3 save-point tags |
| `media-pipeline/` | Scripts that recorded and edited the product videos and music, plus the account-layer test |
| `issues-for-separate-fixes.md` | Security findings to fix separately |

### Branches for `filpl/captureiv` (production)

Each branch starts from `main`. Open one PR per branch, in this order:

1. **`feature/viewer-security-step1`**: the client viewer needs the share link *and* the code; old `/project/CODE` links no longer reveal the share link; each link locks for 1 hour after 10 wrong codes; viewer sessions expire after 12 h; security headers. 8 new tests.
2. **`feature/legal-pages`**: `/legal` pages (Terms, Privacy, Cookies, Billing, Refunds, Copyright, Accessibility), all policy links pointing to them, consent on employee and Enterprise setup, and a clearly shown arbitration and class-action-waiver section. They show a **draft banner** until `LEGAL_TERMS_APPROVED=1`. 7 new tests. **Have a lawyer review before approving.**
3. **`feature/viewer-layout`** (includes `feature/ui-refresh`): the new logo across the app, and the redesigned client viewer (top navbar, calendar, flight library, video pop-up, compare, footer logo). Tabs are limited to what the link allows, and clients still never see documents.
4. **`feature/worker-accounts`**: workers can add flight days (routes plus route videos), edit footage details and upload or edit documents, **on their assigned projects only**. Admins and workers share the same Workspace (Videos & routes + Documents), and the admin keeps its oversight tools. **Fixes a live bug:** worker uploads on the current production code saved nothing. 7 new tests.

`preview/all-changes` combines all four, with the merge conflicts already resolved. Use it to try everything together, or merge it if you'd rather do one PR.

Test results: every test module matches `main` except for the new tests. Two failures already existed on `main` and are unrelated: `test_launch_diagnostics` (in-memory database check) and the rate-limit pruning timing test.

## Applying it

From a clone of `filpl/captureiv`:

```bash
git fetch origin main
git fetch /path/to/captureiv-changes.bundle 'refs/heads/*:refs/heads/*'
git push -u origin feature/viewer-security-step1 feature/legal-pages feature/viewer-layout feature/worker-accounts
# then open the four PRs on GitHub
```

Or with the patch files: `git checkout -b feature/worker-accounts main && git am patches/worker-accounts/*.patch`, and the same for each folder.

The `filpl/captureiv-2` branches: `git fetch /path/to/redesign-branches.bundle 'refs/heads/*:refs/heads/*' 'refs/tags/*:refs/tags/*'`.

## After merging (Render deploys `main`)

Render settings to add (all optional): `LEGAL_ENTITY_NAME`, `LEGAL_POSTAL_ADDRESS`,
`LEGAL_GOVERNING_LAW`, `LEGAL_ARBITRATION_PROVIDER`, `LEGAL_ARBITRATION_LOCATION`, and
`LEGAL_TERMS_APPROVED=1` only after legal review. Stripe, R2, SMTP and Google Maps settings don't change.

Checks:
- `https://app.captureiv.com/api/health` returns `{"status":"ok"}`
- **Maps:** the project map loads with no key errors in the browser console. The new Referrer-Policy still sends the origin to Google.
- **Client code gate:** in a private window, the share link + code opens the viewer; the code alone on the home page does not.
- **Worker:** sign in as a worker, then add a route with a throwaway video and upload a throwaway document on an assigned project. Both should save; an unassigned project should not appear.
- **Stripe:** a test purchase only on a staging service with **test** keys, never live mode without an explicit OK.

To roll back, revert the merge commit on `main` and Render redeploys the previous version.
