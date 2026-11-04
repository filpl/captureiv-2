# Capture IV — issues logged during the User Platform redesign

None of these were changed on `user-platform-ui-redesign`, which is a visual-only branch.
Line references are to `app.py` and the static files at commit `6370bbb`.

## Security (handle on a separate branch)

| # | Issue | Where | Evidence |
|---|---|---|---|
| S1 | The 4-letter code alone opens a project. The share token isn't needed, even though the README says both are. | `index()` `app.py:1619`, `project_view()` `app.py:1659` | Verified live: a fresh visitor typing only the code reached `/share/<token>`. |
| S2 | Codes are guessable: 24⁴ ≈ 332k values in one namespace for all tenants, stored unhashed. Only `POST` is rate-limited (20 per 10 min per IP). `GET /project/<code>` has no limit and works as a code checker. | `create_project_access` `app.py:3712`, `rate_limit_sensitive_routes` `app.py:800` | Code review; the POST limit was observed returning 429. |
| S3 | Any company admin can read every company's audit log (`AuditLog` isn't company-scoped). | `api_audit` (~`app.py:4866`), `TENANT_MODELS` (~432) | Code review |
| S4 | The "Media" sharing switch isn't enforced on file downloads, and the map tab always lists videos. | `protected_file` (~`app.py:3196`) | Code review |
| S5 | No CSP, X-Frame-Options or HSTS. CDN scripts (unpkg) load without SRI. Session not regenerated at login. Audit log trusts raw `X-Forwarded-For`. | `app.py` (no `after_request`), templates | Code review |
| S6 | Admin-reset passwords need only 10 characters, against 12 elsewhere. Some flash messages include raw exception text. | `app.py` | Code review |

## Functional bugs (not security; also out of scope for the redesign)

| # | Issue | Where |
|---|---|---|
| F1 | Saving viewer access for an existing project rotates both code and link; the old link returns 404. | `app.py:3711-3725` (verified live) |
| F2 | On a fresh install, the documented `ADMIN_USERNAME` account is logged out right after signing in, because it has no company membership. | `init_db`, `enforce_workspace_billing_window` (~`app.py:843`) (verified live) |
| F3 | Site-image placement is stored only in the admin's browser, so routes are misaligned in the viewer. | `static/site-setup.js`, `static/project-viewer-map.js` `fitSiteImage` (verified live) |
| F4 | Compare shows "No flight routes are available for this date" over panes that do show routes. The CSS is correct, so this is JavaScript logic. | `static/project-viewer-map.js` (`compare-empty-*` visibility) |
| F5 | Uploading a site reference sends the admin to the "Upload footage" tab. | `upload_project_map` `app.py:4227` redirect (verified live) |
| F6 | When R2 storage is on, route-video upload is rejected: the route direction vocabulary doesn't match `DIRECTIONS`. | `start_r2_upload` `app.py:3978` |
| F7 | Rate-limit cleanup never runs while host uptime is under an hour (`_last_rate_limit_cleanup = 0` vs `time.monotonic()`). This causes 1 failing test. | `app.py:823-830` |
| F8 | Out-of-date test expects `id="upload-progress"`; the template now uses `batchUploadProgress`. | `tests/test_saas_isolation.py:275` |
| F9 | The sidebar heading always reads "Flight Scans", even on Overview, Media and Documents. This is content, not styling, so it was left as is. | `templates/project_view.html` |
| F10 | Leaflet and georaster load only from unpkg.com, with no local fallback. If unpkg is unreachable, the map and the editor fail. | `templates/project_view.html`, `templates/site_capture.html` |
| F11 | Marketing site: missing `</div>` in `landing-page/web/solutions.html` hides the guided-demo caption and the Replay button. | `landing-page/web/solutions.html` |

## Public website findings (logged during `capture-iv-website-redesign`; not changed there)

| # | Issue | Where |
|---|---|---|
| W1 | Contact endpoint accepts requests with no `Origin` header. Origin is only enforced when present, so non-browser clients can bypass it. The rate limit (5/hour per IP) still applies. | `landing-page/worker/contact.js` |
| W2 | Responses set `X-Frame-Options`, `nosniff` and `Referrer-Policy`, but no `Content-Security-Policy` or HSTS. Fonts load from Google Fonts, a third-party request without a CSP allow-list. | `landing-page/scripts/build.mjs` (router), `web/site.css` `@import` |
| W3 | `site.config.json` points login/sign-up links at `http://127.0.0.1:5009`. These must be set to HTTPS production URLs (or the `PLATFORM_*` env vars) before any production build. | `landing-page/site.config.json` |
| W4 | `solutions.html` is missing one `</div>`, which hides the guided-demo caption/Replay button. This is markup, so it was left for a separate fix (it also affects demo cursor positioning). | `landing-page/web/solutions.html` |
| W5 | Content accuracy: "LIVE PROJECT" labels on mock views, LiDAR/3D listed as services, footer reads "© 2024". These are copy decisions, not styling. | `web/index.html`, `web/platform.html`, footers |
| W6 | Stray 366 KB JPEG committed without an extension; not referenced or built. | `landing-page/landing-page` |
