# Not Carried Forward

This template was generalized from a real production app. This file is the **curation record**:
the patterns, dependencies, and config that the source app had but this starter deliberately
**drops or demotes**, with the reasoning. It exists so that future maintainers (and coding
agents) understand that these omissions are intentional, not oversights — and don't "helpfully"
add them back.

The companion docs explain what we *did* keep: [`CLAUDE.md`](./CLAUDE.md),
[`STYLE_GUIDE.md`](./STYLE_GUIDE.md), [`TESTING_GUIDE.md`](./TESTING_GUIDE.md).

---

## Dropped patterns

### 1. Mixed npm/yarn tooling
**Was:** yarn in CI, npm scripts locally, with a yarn lockfile.
**Why dropped:** Source ambiguity and drift. The template **standardizes on npm everywhere** —
`npm ci` in both GitHub Actions workflows, in Husky, and in the Dockerfile — and ships a single
`package-lock.json`. The legacy yarn workflow and frozen-lockfile steps are gone.

### 2. Component-level fetch as the data default
**Was:** No loaders/actions; every page did `useEffect` + `useState` to fetch its data.
**Why dropped (as the default):** Pragmatic for an internal live-polling dashboard, but **route
loaders/actions are the canonical RR7 framework-mode pattern** and the better default for a
teachable template — they give SSR data, automatic revalidation, and progressive enhancement, and
centralize error handling. The example "Items" feature loads via loaders and mutates via actions.
The component-fetch approach is **still documented** as the alternative for live/polling screens in
[`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md); it is simply no longer the default.

### 3. Root-level conditional app chrome
**Was:** `root.tsx` used `isPublicRoute()` to conditionally render a Sidebar / AuthGate /
billing-block modal / route progress bar; a `useMatches()` `layoutMatch` remount key; and a
sidebar-collapse value in `localStorage` with a synchronous `<head>` script to avoid flash.
**Why dropped:** All app-specific auth/layout/tab plumbing. The template keeps a **clean `root.tsx`**
with a *commented* public-vs-authenticated split example and a reference-only
`AuthProvider.example.tsx`. The advanced remount/sidebar recipes live in
[`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md) instead of being baked in.

### 4. Multi-tenant organization plumbing
**Was:** An `OrganizationProvider` with a superadmin org-switcher modal, a `useDateFormatting` hook
that converted Python `strftime` formats to Luxon, and a `useOrgSettings` hook.
**Why dropped:** Tenancy and a Python-`strftime` backend are not universal. The generic
`User`/organization types are minimal; date formatting stays **Luxon-based without strftime
conversion** (the strftime→Luxon converter is documented as an add-on, since generic backends
aren't assumed to be Python).

### 5. Domain feature code
**Was:** Hooks, components, types, and routes for the source domain (lessons, courses, students,
tutors, clients, billing, transcripts, a Calendar, a MarkdownEditor, create-resource modals, etc.).
**Why dropped:** Entirely domain-specific. Replaced by the neutral **"Items"** feature, which
exercises the same patterns (list/detail/form, loader/action round-trip, table, react-select) with
zero domain vocabulary.

### 6. Vendor monitoring & analytics, and hard-on Sentry
**Was:** Amplitude (product analytics + session replay), Microsoft Clarity (session replay/heatmaps),
Intercom (customer support), and an unconditional `Sentry.init`; plus `useMonitoring` /
`usePauseSessionReplay` / `usePageView` hooks with hardcoded page maps and domain-specific
privacy gating (pausing replay on sensitive routes).
**Why dropped:** Vendor lock-in and domain coupling. **Sentry and Logfire are kept as env-gated
optionals** (they self-disable when their env var is unset — see `app/helpers/env.ts` and
`app/helpers/monitoring.ts`). **Amplitude, Clarity, and Intercom are dropped entirely.** A
**provider-agnostic analytics interface** and a privacy-toggle pattern are documented in
[`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md) rather than wired in.

### 7. Heavy / optional UI libraries as hard dependencies
**Was:** `@mdxeditor/editor`, `react-datepicker`, `framer-motion`, and `markdown-to-jsx` as direct
dependencies.
**Why dropped/demoted:** Not core to a generic starter. **`@mdxeditor/editor` is dropped outright**
(heavy, domain-specific rich-text editing). `react-datepicker`, `framer-motion`, and
`markdown-to-jsx` are **demoted to documented optionals** — the `Modal` animates with CSS keyframes
(no `framer-motion`), date inputs can use the native `Date` API, and `prose.css` styles markdown
without a renderer. Add any of them only if a feature needs it.

### 8. Ad-hoc class composition and mixed icon strategies
**Was:** Raw string-concatenation + `.trim()` for building `className`s, and a mix of raw
`lucide-react` imports alongside custom icon components.
**Why dropped:** Inconsistent and error-prone. Reconciled to **one `cn()` helper** (over `clsx`)
for all class composition and **one icon strategy** (the `makeIcon` factory in
`~/components/icons/Icon`).

### 9. Brand design tokens & fonts
**Was:** A brand palette (`brand-grey`/`brand-yellow`/`status-*`), custom `@font-face` brand fonts,
and a typography constraint forbidding bold/semibold weights (the brand font wasn't designed for them).
**Why dropped:** Brand-specific. Replaced with a **generic semantic palette**
(primary/secondary/neutral/success/warning/error), a **system font stack**, and **no font-weight
restriction**. Reskin via the `@theme` block in `app/app.css`.

### 10. Config errors and legacy cruft
**Was:** A `jest.config.cjs` with real bugs (`collectCoverageFrom` declared twice; `collectCoverage`
set `true` then `false`) and a domain-specific env mock in `jest.setup.js`; a legacy `.eslintrc.cjs`
sitting alongside the ESLint 9 flat config; and a Heroku `Procfile` as the deployment contract.
**Why dropped:** Errors and duplication. The template ships **one coherent jest config**, **generic
env handling** (no domain mock in `jest.setup.js`), **only the ESLint 9 flat config**, and the
**Dockerfile as the primary deploy target** (the `Procfile` remains only as an optional PaaS
convenience).

### 11. Magic z-index values and duplicated inline animations
**Was:** Magic `z-index` numbers scattered across components, and `framer-motion` animation objects
duplicated inline in many files.
**Why dropped:** Hard to maintain. The template documents a **z-layer scale in tokens** and, where
animation is used, **shared motion presets** — rather than ad-hoc values sprinkled through
components.

---

## Dropped / demoted dependencies (summary)

| Dependency | Status | Reason |
| --- | --- | --- |
| `@mdxeditor/editor` | **Dropped** | Heavy, domain-specific rich-text editing. |
| `@intercom/messenger-js-sdk` | **Dropped** | Customer-support vendor; purely domain-specific. |
| `@amplitude/unified` | **Dropped** | Analytics vendor lock-in; replaced by a documented provider-agnostic analytics interface. |
| Microsoft Clarity | **Dropped** | Session-replay vendor; domain privacy coupling. |
| `@sentry/react-router` | **Optional** | Kept, but gated behind `VITE_SENTRY_DSN` — not an unconditional `Sentry.init`. |
| `@pydantic/logfire-browser` (+ `@opentelemetry/auto-instrumentations-web`) | **Optional** | Tracing; init only when `VITE_LOGFIRE_TRACE_URL` is set. |
| `framer-motion` | **Optional** | Animation; `Modal` works via CSS keyframes without it. |
| `react-datepicker` | **Optional** | Date inputs; native `Date` API is enough for the example. |
| `markdown-to-jsx` | **Optional** | Only if rendering markdown/prose content. |
| yarn | **Dropped** | Template standardizes on npm (`npm ci` in CI, Husky, Docker; `package-lock.json` committed). |

Default runtime deps that **are** kept: `react`, `react-dom`, `react-router` (+ `@react-router/node`,
`@react-router/serve`), `tailwindcss` (+ `@tailwindcss/vite`), `luxon`, `lucide-react`,
`react-select`, `isbot`, `clsx`.
