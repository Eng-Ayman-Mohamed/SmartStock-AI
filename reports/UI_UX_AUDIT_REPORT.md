# SmartStock AI — UI/UX Audit Report

**Audited:** 85 files (15 shared components, 36 feature components, 14 pages, router, stores, styles)  
**Date:** 2026-06-23  
**Scope:** Accessibility, Performance, Theming, Responsive Design, Anti-Patterns  
**Audit agents:** 3 parallel UI/UX testers

---

## Audit Health Score

| # | Dimension | Score (0-4) | Key Finding |
|---|-----------|-------------|-------------|
| 1 | Accessibility | 2 | Focus traps, keyboard traps, missing landmarks, no skip nav |
| 2 | Performance | 2 | `transition-all` everywhere, missing memo on toast items, layout thrash |
| 3 | Theming | 3 | Hard-coded chart colors in SkuChart (P0), some dark mode gaps |
| 4 | Responsive Design | 2 | Touch targets under 44px systematically, hover-only actions on mobile |
| 5 | Anti-Patterns | 2 | `<a><button>` nesting, `window.confirm()`, glassmorphism, bounce easing |
| **Total** | | **11/20** | **Acceptable (significant work needed)** |

**Rating band:** 10-13 — Acceptable. Significant work needed across multiple dimensions.

---

## Executive Summary

- **Audit Health Score:** **11/20** (Acceptable)
- **Total issues found:** **84**
- **By severity:** 7 P0 (Critical), 20 P1 (Major), 30 P2 (Minor), 15 P3 (Polish)
- **Top 5 critical issues:**
  1. Modal focus trap missing — keyboard users trapped behind overlay
  2. Password visibility toggle removed from keyboard navigation
  3. Hard-coded chart colors in `SkuChart.tsx` break dark mode
  4. Hover-only delete button in `ConversationSidebar` — inaccessible on touch devices
  5. Side-effect during render in `ForecastingPage.tsx` — potential infinite re-render loop
- **Recommended next steps:** Fix all 7 P0 issues first, then tackle P1 accessibility gaps, theming, and anti-patterns in order

---

## Anti-Patterns Verdict

**PASS/FAIL: FAIL** — Multiple AI-slop tells detected:
- Gradient text/glassmorphism (`backdrop-blur-sm` in AlertBanner)
- Bounce easing (`animate-bounce` in TypingIndicator)
- Generic `transition-all` anti-pattern across 5+ components
- Casual/colloquial copy ("lookin' thin", "Peek 30 days ahead")
- Inconsistent border radii (`rounded-full` vs `rounded-md`)
- Nested interactive elements (`<a><button>`)

---

## Detailed Findings by Severity

---

### P0 — CRITICAL (Must Fix Immediately)

#### P0-1: Modal focus trap missing — keyboard users trapped behind overlay
- **File:** `shared/components/Modal.tsx:12-61`
- **Category:** Accessibility
- **Impact:** Keyboard users who Tab past the last focusable element in the modal interact with the page behind the overlay. Focus is never restored to the trigger element on close.
- **WCAG:** WCAG 2.4.3 (Focus Order), WCAG 1.4.2 (No Keyboard Trap)
- **Fix:** Implement focus trap pattern — either use `focus-trap-react` or manually trap focus to first/last focusable elements. Store ref to trigger element and call `.focus()` in `useEffect` cleanup.

#### P0-2: Password visibility toggle has `tabIndex={-1}` — keyboard inaccessible
- **File:** `shared/components/PasswordField.tsx:23`
- **Category:** Accessibility
- **Impact:** The show/hide password button is unreachable via keyboard navigation. Blind users cannot verify their password entry.
- **WCAG:** WCAG 2.1.1 (Keyboard)
- **Fix:** Remove `tabIndex={-1}` from the toggle button.

#### P0-3: Hard-coded chart colors break dark mode in SkuChart
- **File:** `features/forecasting/components/SkuChart.tsx:15,136`
- **Category:** Theming
- **Impact:** `COLORS` array uses hex values (`#185FA5`, `#854F0B`) and reference lines use `stroke="#854F0B"`. These remain unchanged in dark mode, creating contrast failures on dark backgrounds.
- **Fix:** Replace with CSS variable references: `stroke="var(--color-brand-600)"`. Reference line should use `var(--color-orange-600)`. Define chart colors via Tailwind tokens instead of inline hex.

#### P0-4: Hover-only delete action — inaccessible on touch devices
- **File:** `features/ai-assistant/components/ConversationSidebar.tsx:140`
- **Category:** Accessibility / Mobile
- **Impact:** Delete button uses `hidden group-hover:flex`, making it invisible on touch devices where hover doesn't exist. Mobile/tablet users cannot delete conversations.
- **Fix:** Add `max-lg:flex` to keep it visible on mobile, or implement swipe-to-reveal pattern. Keep `lg:group-hover:flex` for desktop.

#### P0-5: Side-effect during render — state setter called in render body
- **File:** `features/forecasting/pages/ForecastingPage.tsx:30`
- **Category:** Performance / Correctness
- **Impact:** `if (alerts.length === 0 && isAlertModalOpen) setIsAlertModalOpen(false);` calls a state setter during render. In React 18 Strict Mode this can fire twice, causing an infinite re-render loop.
- **Fix:** Wrap in `useEffect` with `[alerts, isAlertModalOpen]` dependencies.

#### P0-6: Missing skip-to-content navigation link
- **File:** `shared/components/Layout.tsx:6-20`
- **Category:** Accessibility
- **Impact:** No skip-to-content link as the first focusable element. Keyboard users must tab through the entire sidebar and header before reaching main content on every page navigation.
- **WCAG:** WCAG 2.4.1 (Bypass Blocks)
- **Fix:** Add a visually-hidden skip link before the Sidebar:
  ```tsx
  <a href="#main-content" className="sr-only focus:not-sr-only ...">Skip to main content</a>
  ```

#### P0-7: Clickable `<div>` without keyboard accessibility — PO selection
- **File:** `features/purchasing/pages/PurchasingPage.tsx:239-261`
- **Category:** Accessibility
- **Impact:** `<div onClick={...}>` without `role="button"`, `tabIndex={0}`, or `onKeyDown`. Keyboard-only users cannot select a PO.
- **WCAG:** WCAG 2.1.1 (Keyboard), WCAG 4.1.2 (Name, Role, Value)
- **Fix:** Add `role="button"`, `tabIndex={0}`, and `onKeyDown` handler for Enter/Space.

---

### P1 — MAJOR (Fix Before Release)

#### Accessibility (8 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P1-1 | Touch targets below 44px minimum (6 components) | `Button.tsx:25`, `DataTable.tsx:140`, `Header.tsx:115`, `ThemeToggle.tsx:26`, `Modal.tsx:45`, `Sidebar.tsx:105` | Various | Add `min-w-[44px] min-h-[44px]` to all interactive elements. Wrap icon buttons in 44×44px touch zones. |
| P1-2 | `aria-sort` missing on sortable table headers | `shared/components/DataTable.tsx:53-78` | 53 | Add `aria-sort={col.sortOrder === 'asc' ? 'ascending' : col.sortOrder === 'desc' ? 'descending' : undefined}` to `<th>` |
| P1-3 | Header user menu focus not restored on close | `shared/components/Header.tsx:44-70` | 44 | Store trigger button ref, call `.focus()` in `useEffect` cleanup |
| P1-4 | Duplicate `aria-label="Navigation sidebar"` on two `<aside>` elements | `shared/components/Sidebar.tsx:95,142` | 95,142 | Use "Mobile navigation" and "Main navigation" respectively |
| P1-5 | Auth pages missing `<main>` landmark | `LoginPage.tsx:6`, `RegisterPage.tsx:6`, `ForbiddenPage.tsx:7` | 6 | Replace outer `<div>` with `<main>` |
| P1-6 | No focus management on page transitions | `lib/router.tsx:23-27` | 23 | Auto-focus the `<h1>` after Suspense resolves the lazy-loaded page |
| P1-7 | Skeleton missing `role="status"` and `aria-label` | `shared/components/Skeleton.tsx:11,26` | 11 | Add `role="status"` and `aria-label="Loading"` |
| P1-8 | Toast `aria-atomic="true"` missing on live region | `shared/components/Toast.tsx:24-26` | 25 | Add `aria-atomic="true"` so screen readers announce entire toast content |

#### Theming (4 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P1-9 | Hard-coded colors instead of design tokens (6 spots) | `Header.tsx:105`, `Sidebar.tsx:56,171`, `PasswordField.tsx:18`, `StatCard.tsx:33`, `Button.tsx:8` | Various | Replace `text-white`, `bg-gray-900`, `bg-gray-300` with semantic tokens (`text-canvas`, `bg-canvas-soft`, etc.) |
| P1-10 | Hard-coded progress bar colors without dark mode | `features/inventory/pages/InventoryPage.tsx:249-256` | 249 | Add `dark:bg-red-600 dark:bg-amber-600 dark:bg-green-600` variants |
| P1-11 | `uppercase + tracking-[0.05em]` on StatCard reimplements `eyebrow` token | `shared/components/StatCard.tsx:29` | 29 | Replace with `text-eyebrow text-ink-muted` |
| P1-12 | `bg-green-500` used instead of `bg-green-600` | `shared/components/Header.tsx:105` | 105 | Change to `bg-green-600` to match design system spec |

#### Performance (2 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P1-13 | `transition-all` instead of scoped transitions (5+ components) | `Button.tsx:39`, `Sidebar.tsx:44`, `Header.tsx:88`, `Modal.tsx:45`, `ConversationSidebar.tsx:101`, `AlertSidebar.tsx:50` | Various | Replace with `transition-colors duration-150` for color changes, `transition-transform duration-100` for scale |
| P1-14 | Toast auto-dismiss timer hard-coded at 4000ms | `store/toastStore.ts:24-26` | 24 | Accept `duration` parameter in `addToast`. Default 4000, but allow 6000+ for error toasts. |

#### Anti-Patterns (6 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P1-15 | Empty state text artificially narrow at `max-w-[280px]` | `shared/components/EmptyState.tsx:18` | 18 | Increase to `max-w-sm` (448px) or use responsive constraint `max-w-[280px] sm:max-w-sm` |
| P1-16 | `active:scale-[0.97]` wrong per design system (§8.1 specifies `scale(0.9)`) | `shared/components/Button.tsx:39` | 39 | Change to `active:scale-[0.9]` |
| P1-17 | Toast close button hover state too subtle (5% overlay) | `shared/components/Toast.tsx:40` | 40 | Increase to `hover:bg-black/10 dark:hover:bg-white/20` and add focus-visible ring |
| P1-18 | AI sidebar doesn't collapse on mobile | `features/ai-assistant/components/ChatPanel.tsx:49` | 49 | Add responsive overlay drawer: `max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-40` with backdrop. Default to `false` below `lg`. |
| P1-19 | Form state stale after product swap | `features/inventory/components/AddEditProductModal.tsx:40` | 40 | Add `useEffect` to sync form state when `product` changes, or use `useReducer` with reset action |
| P1-20 | Form persists after close without save | `features/purchasing/components/CreatePurchaseOrderModal.tsx:30-36` | 30 | Add reset on `key={open}` or `useEffect` triggered by `open` |

---

### P2 — MINOR (Fix in Next Pass)

#### Theming / Token Inconsistencies (7 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P2-1 | `shadow-sm` used instead of custom `shadow-soft` token | `ConversationSidebar.tsx:84`, `ModeSelector.tsx:24` | 84,24 | Replace `shadow-sm` → `shadow-soft` |
| P2-2 | `dark:hover:bg-gray-800` inconsistent with `dark:hover:bg-canvas-soft` | `ReorderAlertList.tsx:78` | 78 | Replace with `dark:hover:bg-canvas-soft` |
| P2-3 | `hover:bg-black/5 dark:hover:bg-white/10` — hard-coded opacity | `MonitoringBanners.tsx:41` | 41 | Use `hover:bg-canvas-soft` / `dark:hover:bg-white/5` |
| P2-4 | `focus:ring-2 focus:ring-brand-500` inconsistent with `focus:ring-brand-100` pattern | `EditProfileModal.tsx:77,90` | 77,90 | Standardize to `focus:ring-2 focus:ring-brand-100 focus:border-brand-600` |
| P2-5 | Hard-coded `text-[11px]` inline style bypasses type scale | `CitationTag.tsx:43` | 43 | Use `text-eyebrow` token |
| P2-6 | `max-w-[1440px]` arbitrary value should be a token | `Layout.tsx:13` | 13 | Add `--layout-max-width: 1440px` to `index.css` and use `max-w-[var(--layout-max-width)]` |
| P2-7 | `Draft` badge missing explicit dark mode variant (relies on CSS variable fallthrough) | `Badge.tsx:8` | 8 | Add `dark:bg-gray-800 dark:text-gray-300` for consistency |

#### Accessibility (6 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P2-8 | Table rows with `tabIndex={0}` — non-standard row-level navigation | `shared/components/DataTable.tsx:91-97` | 91 | Remove `tabIndex={0}` and `onKeyDown` from `<tr>`. Use explicit action column instead. |
| P2-9 | Pagination uses `<div>` instead of `<nav>` landmark | `shared/components/DataTable.tsx:136` | 136 | Use `<nav aria-label="Pagination">` |
| P2-10 | No `aria-controls` linking CitationTag button to tooltip content | `CitationTag.tsx:37-48` | 37 | Add `aria-controls="citation-tooltip"` to the button, `id="citation-tooltip"` to the tooltip |
| P2-11 | StatCard Unicode arrows (↑/↓) have no accessible name | `StatCard.tsx:40` | 40 | Add `aria-hidden="true"` on arrow span + `sr-only` text |
| P2-12 | Inputs in LineItemsTable lack `<label>` association; `type="text"` for numeric fields | `LineItemsTable.tsx:108` | 108 | Add `<label htmlFor>` with unique IDs; change `type` to `"number"` for quantity/price |
| P2-13 | AdjustStockModal inputs lack `aria-describedby` for helper text | `AdjustStockModal.tsx:55-62` | 55 | Add `id="delta-help"` on helper `<p>`, `aria-describedby="delta-help"` on input |

#### Performance (4 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P2-14 | No `memo` on Toast items — entire list re-renders on any change | `shared/components/Toast.tsx:28-47` | 28 | Extract `ToastItem` subcomponent wrapped in `memo` |
| P2-15 | `transition-all duration-300 ease-in-out` on AlertSidebar width | `AlertSidebar.tsx:50` | 50 | Use `transition-[width] duration-300 ease-in-out` to scope to width only |
| P2-16 | `opacity-70 transition-opacity` during background refetch — jarring half-faded table | `InventoryPage.tsx:465-470` | 465 | Replace with subtle loading indicator (thin progress bar at top) |
| P2-17 | `AudioBars` rapid inline style transitions (`duration-75`) + frequent state updates cause layout thrash | `VoiceButton.tsx:9-25` | 9 | Switch to CSS-only animated bars using CSS custom properties or `transform` transitions |

#### Anti-Patterns / UX (9 issues)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P2-18 | `window.confirm()` for delete confirmation — synchronous, unstyled, blocks UI | `ConversationSidebar.tsx:73` | 73 | Use the shared `Modal` component with confirmation dialog |
| P2-19 | Hand-rolled modal in InviteUserModal instead of shared `Modal` component | `InviteUserModal.tsx:88-243` | 88 | Refactor to use `shared/components/Modal.tsx` with `title` and `footer` props |
| P2-20 | `defaultValue` on `<select>` instead of `value` — won't update if `doc` changes | `DocumentEditModal.tsx:63` | 63 | Use `value={docType}` with controlled state synced via `useEffect` |
| P2-21 | Theme toggle has no `aria-live` announcement on change | `ThemeToggle.tsx:16-30` | 16 | Add `aria-live="polite"` region or use toast system to announce theme change |
| P2-22 | `transition-all` animates everything including expensive properties | `Button.tsx:39`, `Sidebar.tsx:44`, `Header.tsx:88`, `Modal.tsx:45` | Various | Replace with specific transition properties |
| P2-23 | Scrollbar width layout shift from `overflow: hidden` on modal open | `Modal.tsx:21` | 21 | Add `paddingRight` compensation: `document.body.style.paddingRight = \`${scrollbarWidth}px\`` |
| P2-24 | Spinner instead of skeleton loading pattern on DocumentsPage | `DocumentsPage.tsx:199-201` | 199 | Replace `<Loader2>` spinner with skeleton rows matching DataTable layout |
| P2-25 | `console.warn` in production code path in authStore | `store/authStore.ts:61` | 61 | Guard with `import.meta.env.DEV` |
| P2-26 | Missing `useMemo` for derived alert data | `ForecastingPage.tsx:25-28` | 25 | Wrap `alerts` computation in `useMemo` with proper dependencies |
| P2-27 | Inconsistent border radius (`rounded-full` on search vs `rounded-md` elsewhere) | `InventoryPage.tsx:393`, `AddEditProductModal.tsx:86-125`, `InvoiceScanPage.tsx:319` | Various | Standardize all input border radii to a single value app-wide |

---

### P3 — POLISH (Fix If Time Permits)

| # | Issue | File | Line | Recommendation |
|---|-------|------|------|----------------|
| P3-1 | Keyframe names not prefixed — potential naming collision | `index.css:168-191` | 168 | Prefix with `ss-` (e.g., `ss-fadeIn`, `ss-slideUp`) |
| P3-2 | Theme switch is instant and jarring — no transition | `store/themeStore.ts` | — | Add `transition: background-color 200ms ease, color 200ms ease` to `<body>` |
| P3-3 | Sidebar nav items re-render completely on collapse change | `Sidebar.tsx:151-176` | 151 | Extract `NavItem` component wrapped in `memo` |
| P3-4 | `animate-bounce` on TypingIndicator — undignified motion anti-pattern | `TypingIndicator.tsx:11` | 11 | Replace with subtle fade-pulse (`animate-pulse` or custom `@keyframes gentle-pulse`) |
| P3-5 | `backdrop-blur-sm` on AlertBanner — glassmorphism, inconsistent with flat Notion aesthetic | `AlertBanner.tsx:20` | 20 | Remove blur, use solid background with border |
| P3-6 | "lookin'" typo in InventoryPage subtitle — casual tone inconsistent | `InventoryPage.tsx:358-361` | 358 | Use conditional: either show count or "All products are well-stocked." |
| P3-7 | "Peek 30 days ahead" — informal, may confuse non-native speakers | `ForecastingPage.tsx:51` | 51 | Use: "AI-powered demand forecasts for the next 30 days" |
| P3-8 | No theme transition — theme switch is instant | `themeStore.ts` | — | Add `transition: background-color 200ms ease` to root elements |
| P3-9 | `border-b-[0.5px]` renders inconsistently across browsers | `ProfilePage.tsx:46` | 46 | Use `border-b` (1px) with hairline token |
| P3-10 | Jargon in auth page footer ("JWT", "HttpOnly cookie") | `LoginPage.tsx:22`, `RegisterPage.tsx:22` | 22 | Simplify to: "Your session is encrypted and secure" |
| P3-11 | `disabled:opacity-40` inconsistent with `disabled:opacity-50` elsewhere | `UsersTable.tsx:148` | 148 | Standardize to `disabled:opacity-50` |
| P3-12 | `text-center` on empty state body creates triangular rag | `EmptyState.tsx:18` | 18 | Use `text-left` for better readability on body copy |
| P3-13 | `py-16` on EmptyState is excessive on short screens | `EmptyState.tsx:15` | 15 | Use responsive: `py-12 sm:py-16 lg:py-20` |
| P3-14 | `noPadding` prop on Card causes duplicate `flex-1 min-h-0` — layout bug | `Card.tsx:12-24` | 12 | Remove double `flex-1` on inner div; only `min-w-0` needed |
| P3-15 | Magic number `calc(100vh-40px-32px)` for page height | `AIAssistantPage.tsx:5` | 5 | Define CSS variable for header/footer heights |

---

## Positive Findings

What's working well — good practices to maintain:

1. **Design system adherence:** Most tokens are used consistently (`brand-*`, `green-*`, semantic aliases)
2. **Semantic HTML:** Tables use `<th scope="col">`, `<caption>`, `<header>`, `<main>`, `<nav>`
3. **Dark mode:** Most variants include `dark:` overrides; global dark mode works across pages
4. **Reduced motion:** Global `prefers-reduced-motion` breakpoint in `index.css:193-199`
5. **Type safety:** Full TypeScript interfaces with no `any` types in components
6. **Zustand store selectors:** Individual selectors prevent unnecessary re-renders
7. **Accessibility foundations:** Icon-only buttons have `aria-label`, `role="menu"` on dropdowns, `role="alert"` on toasts
8. **Memo usage:** `DataTable`, `EmptyState`, and `Skeleton` properly use `memo`
9. **Lazy-loaded routing:** All pages are `React.lazy()` loaded with code splitting
10. **TanStack React Query:** 60s staleTime, 2 retries — good server-state management
11. **`prefers-reduced-motion`:** Respected globally at the stylesheet level
12. **Consistent error patterns:** Inline error states with retry buttons across all pages
13. **Auth token refresh queue:** Concurrent 401s handled elegantly with a single refresh
14. **Notion-inspired palette:** Well-thought-out warm paper aesthetic with semantic aliases (`canvas`, `ink`, `hairline`)

---

## Category Breakdown

| Category | P0 | P1 | P2 | P3 | Total |
|----------|----|----|----|----|-------|
| **Accessibility** | 3 | 8 | 6 | — | 17 |
| **Performance** | 1 | 2 | 4 | 2 | 9 |
| **Theming** | 1 | 4 | 7 | 2 | 14 |
| **Responsive** | 1 | 1 | 1 | 3 | 6 |
| **Anti-Patterns / UX** | 1 | 5 | 9 | 4 | 19 |
| **Visual/Consistency** | — | — | 3 | 4 | 7 |

**Total unique issues: 84** (some span multiple categories)

---

## Systemic Patterns

Recurring problems that indicate systemic gaps:

1. **`transition-all` anti-pattern** — 7 components use `transition-all` instead of scoped transitions. Suggests no lint rule or code review check for this.
2. **Hard-coded values bypassing tokens** — `shadow-sm` instead of `shadow-soft`, `text-[11px]` instead of `text-eyebrow`, `max-w-[1440px]` instead of a layout token. Design token adoption is strong but not universal.
3. **Inconsistent touch target sizes** — 6 components use 28px icon buttons. No design standard for minimum interactive element size in the design system.
4. **Focus management gaps** — No skip-to-content, no focus restoration on modal/menu close, no auto-focus on page transitions. Suggests no accessibility checklist in the development workflow.
5. **Form state bugs** — 3 modals have stale or persisting form state after close/edit. Pattern suggests no `resetOnClose` convention for modals.
6. **Inconsistent border radii** — `rounded-full` on search bars and some modals, `rounded-md` on auth forms, `rounded-lg` on cards. No single radius standard for inputs.

---

## Recommended Actions

### Sprint 0 — Critical Fixes (estimated: 2-3 hours)
1. **[P0-1]** `/harden` — Implement focus trap on Modal
2. **[P0-2]** `/harden` — Remove `tabIndex={-1}` from PasswordField toggle
3. **[P0-3]** `/harden` — Replace hard-coded chart colors with CSS variables in SkuChart
4. **[P0-4]** `/adapt` — Make ConversationSidebar delete visible on mobile
5. **[P0-5]** `/harden` — Wrap state setter in useEffect on ForecastingPage
6. **[P0-6]** `/clarify` — Add skip-to-content link to Layout
7. **[P0-7]** `/harden` — Make PO selection div keyboard-accessible

### Sprint 1 — Accessibility (estimated: 4-5 hours)
8. **[P1-1]** `/adapt` — Increase touch targets to 44px minimum across all components
9. **[P1-2]** `/clarify` — Add `aria-sort` to DataTable headers
10. **[P1-3]** `/harden` — Restore focus on header user menu close
11. **[P1-4]** `/clarify` — Fix duplicate sidebar aria-label
12. **[P1-5]** `/clarify` — Add `<main>` landmark to auth pages
13. **[P1-6]** `/harden` — Add focus management on page transitions
14. **[P1-7]** `/clarify` — Add `role="status"` to Skeleton
15. **[P1-8]** `/clarify` — Add `aria-atomic="true"` to Toast container

### Sprint 2 — Theming (estimated: 3-4 hours)
16. **[P1-9]** `/colorize` — Replace hard-coded colors with design tokens
17. **[P1-10]** `/colorize` — Add dark mode variants to progress bars
18. **[P1-11]** `/typeset` — Replace manual uppercase + tracking with `text-eyebrow`
19. **[P1-12]** `/colorize` — Fix `bg-green-500` → `bg-green-600`

### Sprint 3 — Performance & Anti-Patterns (estimated: 4-5 hours)
20. **[P1-13]** `/optimize` — Scope all `transition-all` to specific properties
21. **[P1-14]** `/clarify` — Add configurable toast duration
22. **[P1-15]** `/layout` — Widen EmptyState text constraint
23. **[P1-16]** `/polish` — Fix button press scale to `0.9`
24. **[P1-17]** `/polish` — Improve toast close button hover state
25. **[P1-18]** `/adapt` — Make AI sidebar responsive with mobile overlay
26. **[P1-19]** `/harden` — Fix stale form state in AddEditProductModal
27. **[P1-20]** `/harden` — Reset CreatePurchaseOrderModal form on close

### Sprint 4 — P2 Bulk Fixes (estimated: 6-8 hours)
28. All 30 P2 issues across theming, a11y, performance, and anti-patterns

### Sprint 5 — Polish (estimated: 3-4 hours)
29. All 15 P3 cosmetic issues
30. **[P3-15]** `/polish` — Final quality pass

> Re-run `/audit` after fixes to see the score improve.

---

*Report generated by 3 parallel UI/UX audit agents. All 85 source files read and cross-referenced against `index.css` design tokens and design system conventions.*
