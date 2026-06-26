# Storybook Setup Report

## Date
2026-06-26

## Objective
Set up Storybook for component documentation and visual regression testing on the SmartStock frontend.

## Stack

| Tool | Version | Purpose |
|---|---|---|
| `storybook` | 10.4.6 | Core framework |
| `@storybook/react-vite` | 10.4.6 | React + Vite integration |
| `@storybook/addon-a11y` | 10.4.6 | Accessibility panel per story |
| `@storybook/addon-vitest` | 10.4.6 | Vitest test runner integration |
| `@storybook/test-runner` | latest | Headless Playwright-based story runner |
| `playwright` | 1.61.1 | Browser automation for visual regression |

## Key Decisions

### Why not `@storybook/addon-essentials`?
Since Storybook 9, `@storybook/addon-essentials` is an **empty package** — all its features (controls, actions, backgrounds, docs, viewport, toolbars) are built into Storybook core. No need to install it.

### Why not Loki for visual regression?
Loki 0.35.1 (latest, Aug 2024) is effectively **unmaintained** (no commits in 12+ months, 140 open issues). It relies on `window.__STORYBOOK_CLIENT_API__` which was removed in Storybook 8+. Issue [#550](https://github.com/oblador/loki/issues/550) documents incompatibility with Storybook 10. Replaced with `@storybook/test-runner` + Playwright, which generates screenshots per story for visual diffing.

### Tailwind CSS v4 integration
Tailwind v4 uses the `@tailwindcss/vite` plugin (no PostCSS). Storybook's Vite builder auto-merges `vite.config.ts`, so the plugin is picked up automatically. The CSS is imported in `.storybook/preview.tsx` via `import '../src/index.css'`.

### TypeScript 6.0 + verbatimModuleSyntax
The project uses TypeScript 6.0 with `verbatimModuleSyntax: true` and `erasableSyntaxOnly: true`. These settings match [Storybook's recommended tsconfig](https://github.com/storybookjs/storybook/discussions/33249). All known internal violations were fixed in Storybook 9/10. No compatibility issues found.

### State mocking for stories
The `authStore` imports `axios` and makes live HTTP calls. A `withMockAuth` decorator was created to inject a mock user into the store before story render. Three other decorators handle routing (`withRouter`), query client (`withQueryClient`), and toast state (`withToast`).

## Files Created

### Configuration (`.storybook/`)

| File | Content |
|---|---|
| `main.ts` | Framework `@storybook/react-vite`, a11y + vitest addons, `viteFinal` with `@tailwindcss/vite` plugin |
| `preview.tsx` | Tailwind CSS import, dark mode toolbar toggle via `globalTypes`, global `withRouter` decorator |
| `test-runner.ts` | Playwright `postVisit` hook — takes full-page screenshot per story |

### Utilities

| File | Content |
|---|---|
| `src/shared/test-utils/decorators.tsx` | `withRouter` (MemoryRouter), `withQueryClient` (QueryClientProvider), `withMockAuth` (mock user in authStore), `withToast` (toast store setup) |

### Story Files — 24 files, ~60 story variants

#### Batch 1: Shared Primitives (10 files)

| File | Stories |
|---|---|
| `Button.stories.tsx` | 5 variants × 3 sizes, 3 disabled states |
| `Badge.stories.tsx` | 13 status/role variants, with/without dot |
| `Card.stories.tsx` | Default, with subtitle, with action, no title, noPadding |
| `Modal.stories.tsx` | Default, with footer, long content, no title, interactive |
| `EmptyState.stories.tsx` | Default, with action, search empty, no documents |
| `Skeleton.stories.tsx` | Block, small block, 3 lines, 5 lines, card skeleton |
| `StatCard.stories.tsx` | Default, with icon, up/down trend, green/red/purple accent |
| `PasswordField.stories.tsx` | Default, with value, disabled, error, custom placeholder |
| `DataTable.stories.tsx` | Populated, empty, loading, with pagination, sortable |
| `Toast.stories.tsx` | Success, error, info, stacked, interactive |

#### Batch 2: Layout Components (5 files)

| File | Stories | Decorators |
|---|---|---|
| `Sidebar.stories.tsx` | Default (manager role) | `withRouter`, `withMockAuth` |
| `Header.stories.tsx` | Default (admin user) | `withRouter`, `withMockAuth` |
| `ThemeToggle.stories.tsx` | Default | `withRouter` |
| `NotificationItem.stories.tsx` | Info unread, warning, critical, read, escalation | `withMockAuth` |
| `NotificationEmpty.stories.tsx` | Default | — |

#### Batch 3: Feature Components (9 files)

| Feature | File | Stories |
|---|---|---|
| AI Assistant | `MessageBubble.stories.tsx` | User message, AI simple, with citation, multiple citations, streaming placeholder |
| AI Assistant | `TypingIndicator.stories.tsx` | Default |
| AI Assistant | `ChatEmptyState.stories.tsx` | Default with suggestions |
| AI Assistant | `VoiceButton.stories.tsx` | Default (idle state) |
| AI Assistant | `ModeSelector.stories.tsx` | Auto, NL query, RAG, interactive |
| Forecasting | `AlertBanner.stories.tsx` | Critical, warning |
| Purchasing | `POApprovalCard.stories.tsx` | Default, read-only, with long reasoning |
| Users | `RoleBadge.stories.tsx` | Viewer, manager, admin |
| Auth | `LoginForm.stories.tsx` | Default (empty form) |

## Modifications to Existing Files

| File | Change |
|---|---|
| `package.json` | Added scripts: `storybook`, `build-storybook`, `test-storybook`, `test-storybook:ci` |
| `package.json` | Added devDependencies: `storybook`, `@storybook/react-vite`, `@storybook/addon-a11y`, `@storybook/addon-vitest`, `@storybook/test-runner`, `playwright`, `start-server-and-test` |
| `eslint.config.js` | Added `storybook-static` to `globalIgnores` |

## Commands

```bash
# Development
npm run storybook                    # starts dev server at http://localhost:6006

# Static build
npm run build-storybook              # outputs to storybook-static/

# Visual regression tests
npm run test-storybook               # runs Playwright against running storybook
npm run test-storybook:ci            # starts storybook, runs tests, then stops

# Verification
npm run lint                         # eslint — passes clean
npm run build-storybook -- --quiet   # builds without errors
```

## Verification Results

| Check | Status |
|---|---|
| `npm run build-storybook` | ✅ Passes — 1948 modules transformed |
| `npm run lint` | ✅ Passes — 0 errors, 0 warnings |
| Dev server (`:6006`) | ✅ Responds HTTP 200 |
| Dark mode toggle | ✅ Toolbar button toggles `.dark` class |

## Future Work

- Add visual baseline snapshots: run `npm run test-storybook` once, commit `__snapshots__/` directory as baseline
- CI integration: add `npm run test-storybook:ci` to `.github/workflows/ci.yml`
- Add more feature stories for remaining components (ChatPanel, ConversationSidebar, UsersTable, etc.)
- Add interaction tests (play functions) for form submission flows
