# SmartStock AI — Design System Prompt

# For use with Figma AI, Galileo AI, Uizard, Locofy, or any AI design tool

---

## PROJECT CONTEXT

You are designing **SmartStock AI**, a B2B SaaS warehouse inventory management dashboard for warehouse managers and procurement teams at medium-to-large e-commerce businesses. The product is desktop-first, data-dense, and used daily by non-technical operations staff. The UI must feel professional, trustworthy, and efficient — inspired by **Notion's warm paper-calm aesthetic**. Clean, quiet chrome with a single confident blue accent, decorated by a playful multi-color sticker palette that adds personality without painting structure. Avoid gradients, heavy shadows, and anything that prioritises aesthetics over readability.

---

## 1. BRAND IDENTITY

**Product name:** SmartStock AI
**Tagline:** Proactive demand planning — know what you need before you run out.
**Personality:** Confident, precise, intelligent, calm under pressure.
**Tone:** Professional but approachable. Clear, direct, data-forward.
**Primary audience:** Warehouse managers, 25–50 years old, desktop-only, working in fast-paced logistics environments.

---

## 2. COLOR SYSTEM

### Foundations

The palette is adapted from Notion's design language: a warm off-white canvas, near-black Inter type, a single confident blue for actions, and a multi-color sticker palette that carries all personality while the chrome stays quiet. Semantic colors (success, warning, danger, AI) are mapped to the sticker palette.

### Surface & Text

| Token          | Hex     | Usage                             |
|----------------|---------|-----------------------------------|
| canvas         | #FFFFFF | Card backgrounds, panels, sidebar |
| canvas-soft    | #F6F5F4 | Page background                   |
| hairline       | #E6E6E6 | Borders, dividers, table rules    |
| ink            | #000000 | Headings                          |
| ink-secondary  | #31302E | Secondary body text               |
| ink-muted      | #615D59 | Muted text, metadata              |
| ink-faint      | #A39E98 | Placeholder text, disabled labels |

### Primary — Notion Blue

| Token         | Hex        | Usage                             |
|---------------|------------|-----------------------------------|
| brand-50      | #EEF5FF    | Button hover bg, info backgrounds |
| brand-100     | #D9E8FF    | Borders on info cards, focus ring |
| brand-400     | #4A9EF5    | Hover states                      |
| brand-600     | #0075DE    | Primary buttons, active nav items |
| brand-800     | #005BAB    | Pressed state, text on brand-50   |
| brand-900     | #003F82    | Darkest text on light brand fills |

### Success — Sticker Green

| Token     | Hex        | Usage                    |
|-----------|------------|--------------------------|
| green-50  | #E8F5E9    | Success background fills |
| green-200 | #A5D6A7    | Success borders          |
| green-600 | #1AAE39    | Success badge text       |
| green-800 | #1B5E20    | Text on green-50         |

### Warning — Sticker Orange

| Token      | Hex        | Usage                       |
|------------|------------|-----------------------------|
| orange-50  | #FFF3E0    | Warning background fills    |
| orange-100 | #FFCC80    | Warning borders, icon fills |
| orange-600 | #DD5B00    | Warning badge text          |
| orange-800 | #E65100    | Text on orange-50           |

### Danger — Red

| Token   | Hex        | Usage                   |
|---------|------------|-------------------------|
| red-50  | #FFEBEE    | Danger background fills |
| red-200 | #EF9A9A    | Danger borders          |
| red-600 | #E53935    | Danger badge text       |
| red-800 | #C62828    | Text on red-50          |

### AI / Forecasting — Sticker Purple

| Token     | Hex        | Usage                          |
|-----------|------------|--------------------------------|
| purple-50 | #F3E5F5    | AI feature backgrounds         |
| purple-100| #E1BEE7    | AI borders                     |
| purple-600| #D6B6F6    | AI badge text, forecast labels |
| purple-800| #391C57    | Text on purple-50              |

### Sticker Palette (Decorative)

Notion's playful multi-color palette — used for illustrations, icon tiles, and decorative dots. **Never for CTAs or structural fills.**

| Name          | Hex        | Usage                    |
|---------------|------------|--------------------------|
| sticker-sky   | #62AEF0    | Chart accents, decorative|
| sticker-pink  | #FF64C8    | Accent illustrations     |
| sticker-teal  | #2A9D99    | Secondary accents        |
| sticker-brown | #523410    | Neutral decorative       |

> Semantic colors (green, orange, purple) already use their matching sticker-palette values.

### Semantic color rules

- **Never use color alone** to convey status — always pair with an icon or text label.
- **AI-generated content** always uses purple tokens. Users learn: purple = AI.
- **Text on colored backgrounds** must always use the 800 stop of that same ramp.
- **Contrast ratio:** all text/background pairs must meet 4.5:1 minimum (WCAG AA).
- **The sticker palette** is decoration only — never for CTAs, nav items, or form borders.

---

## 3. TYPOGRAPHY

### Font stack

- **Primary:** `"Inter", -apple-system, system-ui, "Segoe UI", Helvetica, Arial, sans-serif`
- **Monospace:** `"Cascadia Code", "Fira Code", "Courier New", monospace` — used for SKU codes, PO numbers, API keys

### Type scale

Adapted from Notion's broader marketing scale for a data-dense dashboard.

| Role            | Size | Weight | Line Height | Letter Spacing | Usage                             |
|-----------------|------|--------|-------------|----------------|-----------------------------------|
| Page heading    | 22px | 700    | 1.27        | -0.25px        | Dashboard page titles             |
| Section heading | 18px | 600    | 1.33        | 0              | Card headings, section titles     |
| Card title      | 15px | 500    | 1.4         | 0              | Table headers, panel titles       |
| Body            | 14px | 400    | 1.5         | 0              | All body copy, table cell data    |
| Caption         | 12px | 400    | 1.43        | 0              | Timestamps, metadata, helper text |
| Eyebrow         | 11px | 600    | 1.33        | +0.125px       | Badge labels, small metadata      |
| Monospace       | 12px | 400    | 1.5         | 0              | SKU codes, PO numbers, IDs        |

### Typography rules

- Use **sentence case** everywhere. Never ALL CAPS or Title Case in UI.
- Numbers in tables and stat cards use **tabular figures** (`font-variant-numeric: tabular-nums`) so columns align.
- Truncate long text with ellipsis (`…`) — never wrap text inside table cells.
- Minimum font size: **11px**. Never smaller.
- Page headings use Notion-style tight negative tracking (`-0.25px` at 22px).
- Weight contrast is the primary expressive lever: 700 for headings, 400 for body.

---

## 4. SPACING SYSTEM

Base unit: **8px**. All spacing is a multiple of 8 (with occasional 4px adjustments for tight spots).

| Token    | Value | Common usage                             |
|----------|-------|------------------------------------------|
| space-0.5| 4px   | Tight icon-label gap, badge inner pad    |
| space-1  | 8px   | Input inner padding, tight row gap       |
| space-2  | 16px  | Default component gap                    |
| space-3  | 24px  | Card internal padding, section gap       |
| space-4  | 32px  | Page horizontal margin                   |
| space-5  | 40px  | Section vertical gap                     |
| space-6  | 48px  | Page vertical spacing                    |

---

## 5. BORDER RADIUS

| Token       | Value  | Usage                           |
|-------------|--------|---------------------------------|
| radius-xs   | 4px    | Form fields, small tags         |
| radius-sm   | 5px    | Menu items, list rows           |
| radius-md   | 8px    | Utility buttons, smaller cards  |
| radius-lg   | 12px   | Feature cards, modal surfaces   |
| radius-xl   | 16px   | Large containers, image wells   |
| radius-full | 9999px | Pill CTAs, badges, avatars      |

---

## 6. SHADOWS & ELEVATION

Notion's elevation philosophy: **barely-there**. Surfaces are gently lifted off the canvas rather than heavily dropped. Built from multiple near-transparent layers.

| Level      | Style                                                                        | Usage                      |
|------------|------------------------------------------------------------------------------|----------------------------|
| Flat       | Hairline border `hairline`, no shadow                                        | Cards, table rows          |
| Soft       | `0 0.175px 1.041px rgba(0,0,0,0.01), 0 0.8px 2.925px rgba(0,0,0,0.02), 0 2.025px 7.847px rgba(0,0,0,0.027), 0 4px 18px rgba(0,0,0,0.04)` | Raised cards, dropdowns |
| Elevated   | `0 4px 24px rgba(0,0,0,0.12)`                                                  | Modals, popovers           |
| Focus ring | `0 0 0 3px #D9E8FF`                                                          | All interactive elements   |
| Press      | `scale(0.9)` transform                                                       | Button press feedback      |

---

## 7. LAYOUT & GRID

### App shell structure

```
┌─────────────────────────────────────────────────────┐
│                    Header (40px)                     │
├──────────┬──────────────────────────────────────────┤
│ Sidebar  │                                           │
│ 56px     │          Main Content Area                │
│(collapsed)│         (flex-1, scrollable)             │
│ 220px    │                                           │
│(expanded)│                                           │
└──────────┴──────────────────────────────────────────┘
```

### Sidebar

- Collapsed: **56px wide** — shows icons only
- Expanded: **220px wide** — shows icons + labels
- Transition: `width 200ms ease`
- Background: white (`canvas`) with right border `1px solid hairline`
- Active nav item: `background brand-50, color brand-600, border-left 2px solid brand-600`

### Header

- Height: **40px** (compact — data-heavy tools use space efficiently)
- Background: white (`canvas`), bottom border `1px solid hairline`
- Contains: breadcrumb left, user avatar + role badge right
- Sticky `top: 0, z-index: 10`

### Content grid

- Page max-width: **1440px**, centered
- Page horizontal padding: **32px** (`space-4`)
- Stat card row: `grid, 4 columns, gap: 24px`
- Chart + side panel: `grid, 2fr + 1fr, gap: 24px`
- Full-width table: `100% width`

### Breakpoints

| Name | Width  | Behavior                         |
|------|--------|----------------------------------|
| sm   | 640px  | 1-column grid, sidebar hidden    |
| md   | 768px  | 2-column grid, sidebar icon-only |
| lg   | 1024px | Full layout (primary target)     |
| xl   | 1280px | Wider content, larger charts     |
| 2xl  | 1536px | Centered max-width content       |

---

## 8. COMPONENTS

### 8.1 Button

```
Variants: primary | secondary | danger | ghost | utility
Sizes: sm (28px height) | md (36px height) | lg (44px height)

Primary:
  bg brand-600 (#0075DE), text white, hover bg brand-800
  radius-full (pill shape — Notion's signature CTA style)
  Pressed: scale(0.9) transform, 100ms

Secondary:
  bg white, border hairline, text ink, hover bg canvas-soft
  radius-full (pill)
  Elevation: Soft (layered micro-shadow)

Utility:
  bg white, border hairline, text ink, hover bg canvas-soft
  radius-md (8px — tighter than pill)
  padding: 4px 14px
  Used for nav and secondary select actions

Danger:
  bg red-600, text white, hover bg red-800
  radius-md

Ghost:
  no bg, no border, text brand-600, hover bg brand-50
  radius-md

Disabled:
  bg canvas-soft, text ink-faint, cursor not-allowed

Font: 14px, weight 500 (primary/secondary/danger)
      13px, weight 500 (ghost/utility)
Focus ring: 0 0 0 3px brand-100
```

### 8.2 Badge / Status pill

```
Sizes: small only (inline with text)
Border radius: radius-full (pill — matches Notion badge-pill)
Font: 11px, weight 600, letter-spacing 0.125px (eyebrow style)
Padding: 4px 8px

Status mappings:
  "In Stock"         → bg green-50,  text green-800,  dot green-600
  "Low Stock"        → bg orange-50,  text orange-800,  dot orange-600
  "Out of Stock"     → bg red-50,    text red-800,    dot red-600
  "Draft"            → bg canvas-soft, text ink-muted
  "Pending Approval" → bg orange-50,  text orange-800
  "Approved"         → bg green-50,  text green-800
  "Sent"             → bg brand-50,  text brand-800
  "Confirmed"        → bg green-50,  text green-800
  "Rejected"         → bg red-50,    text red-800
  "AI Generated"     → bg purple-50, text purple-800, sparkle icon
  "Viewer"           → bg canvas-soft, text ink-muted
  "Manager"          → bg brand-50,  text brand-800
  "Admin"            → bg purple-50, text purple-800
```

### 8.3 Input field

```
Height: 36px
Border: 1px solid hairline, radius-xs (4px — tight Notion style)
Background: white
Font: 14px, text ink
Placeholder: ink-faint

States:
  Default: border hairline
  Hover:   border ink-muted
  Focus:   border brand-600, ring 0 0 0 3px brand-100
           Elevation: Soft (layered shadow on focus — Notion style)
  Error:   border red-600, ring 0 0 0 3px red-50
  Disabled: bg canvas-soft, text ink-faint

With label (FormField molecule):
  Label above: 11px, ink-secondary, mb-1
  Error below: 11px, red-600, mt-1, with warning icon
```

### 8.4 Stat card

```
Background: white (canvas)
Border radius: radius-lg (12px — feature-card style)
Elevation: Flat (hairline border only)
Padding: 24px (space-3)
Height: fixed 96px (no layout shift on load)
Min-width: 160px

Structure:
  ↳ Label (11px, ink-secondary, uppercase, letter-spacing 0.05em)
  ↳ Value (24px, weight 500, ink) — uses tabular-nums
  ↳ Trend indicator (11px): ↑ green-600 or ↓ red-600 + percentage
  ↳ Skeleton on load: matches exact dimensions (canvas-soft animated pulse)

Example cards for SmartStock AI:
  "Total SKUs"         value: 1,247        trend: none
  "Low Stock Alerts"   value: 23           trend: ↑ 12% (orange-600)
  "Pending POs"        value: 8            trend: none
  "Forecast Accuracy"  value: 87.4%        trend: ↑ 2.1% (green-600)
```

### 8.5 Data table

```
Table layout: fixed (prevents layout shift on load)
Row height: 44px (single-line data rows)
Header height: 36px

Header row:
  bg canvas-soft, border-bottom 1px hairline
  font: 11px, weight 600, ink-secondary, uppercase, letter-spacing 0.125px (eyebrow)

Data rows:
  bg white, border-bottom 0.5px hairline
  hover: bg canvas-soft
  selected: bg brand-50, border-left 2px brand-600

Column types:
  SKU code → monospace 12px, ink-secondary
  Product name → 14px, ink, truncate with tooltip
  Number / quantity → tabular-nums, right-aligned
  Status → inline Badge component
  Date → 12px, ink-secondary, "DD MMM YYYY" format
  Actions → ghost icon buttons, visible on row hover only

Pagination:
  Below table, right-aligned
  "Showing 1–20 of 1,247 results" (14px, ink-muted)
  Prev / Next buttons (secondary pill variant)
  Page size selector: 20 / 50 / 100 rows
```

### 8.6 Card

```
Background: white (canvas)
Border: 1px solid hairline
Border radius: radius-lg (12px)
Padding: 24px (space-3)
Box shadow: Flat (hairline only) or Soft (layered) for elevated variants

Card header:
  Title: 15px, weight 500, ink
  Subtitle (optional): 12px, ink-muted
  Action (optional): utility button or icon, right-aligned
  Border-bottom: 1px hairline, pb-3 mb-3

Card sections:
  Divider between sections: 1px hairline, my-3
```

### 8.7 Sidebar navigation

```
Item height: 40px
Padding: px-3
Border radius: radius-md (8px)
Font: 14px

States:
  Default:  text ink-secondary, icon ink-secondary (~60% opacity)
  Hover:    bg canvas-soft, text ink, icon ink
  Active:   bg brand-50, text brand-800, icon brand-600
            border-left: 2px solid brand-600

Icon: 18px, Lucide React outline icons
Label: shown when expanded (220px), hidden when collapsed (56px)

Nav items for SmartStock AI:
  🏠 Dashboard      (ti-layout-dashboard)
  📦 Inventory      (ti-package)
  📈 Forecasting    (ti-chart-line)
  🛒 Purchasing     (ti-shopping-cart)
  🤖 AI Assistant   (ti-robot) ← purple accent color
  📄 Invoice Scan   (ti-scan)
  ⚙️  Settings       (ti-settings) ← bottom of sidebar
```

### 8.8 PO Approval Card (HITL component)

```
This is the most important interaction in the product.
The warehouse manager approves or rejects AI-generated purchase orders.

Card style: white (canvas), border-left 3px solid orange-600, radius-lg, Soft elevation
Header: "Purchase Order Draft" (15px, 500) + "AI Generated" badge (purple)

Content rows (label + value pairs, 44px each):
  SKU            monospace 12px
  Product        14px, ink
  Predicted stockout  12px, red-600, with calendar icon
  Recommended qty     16px, 500, ink (editable input field)
  Supplier       14px, ink-secondary
  Estimated cost 16px, 500, ink

Reasoning trace (collapsible):
  "Why did the AI flag this?" accordion
  Body: 12px, ink-muted, italic, bg purple-50, border-left 2px purple-100, p-3

Actions (bottom of card, full-width):
  Reject   → danger ghost button (radius-md)
  Edit Qty → utility button (radius-md)
  Approve  → primary pill button (brand-600)
```

### 8.9 Chat panel (AI Assistant)

```
Container: white card, full-height, flex-col
Height: fills viewport minus header + sidebar

Message bubbles:
  User:  right-aligned, bg brand-600, text white, radius-lg radius-br-sm
  AI:    left-aligned, bg canvas-soft, text ink, radius-lg radius-bl-sm
  Font:  14px, line-height 1.5

Citation tags (inline within AI messages):
  Style: bg purple-50, text purple-800, border 0.5px purple-100
  Format: "[Source: supplier_policy.pdf, Page: 3]"
  Font: 11px, monospace

Input area (bottom of panel):
  Height: 52px
  Input: full-width, 36px height, radius-full (pill)
  Right icons: microphone button (voice) + send button
  Mic active state: red-600 icon with pulse animation

Loading state (AI thinking):
  Three-dot animation in AI message bubble
  bg canvas-soft, dots ink-faint
```

### 8.10 Invoice confirmation card

```
Triggered after GPT-4o Vision extracts data from uploaded invoice.

Layout: 2-column grid
  Left col (50%):  uploaded invoice image (contained, max-h 400px)
  Right col (50%): extracted fields (editable)

Extracted field rows:
  Label (11px, ink-secondary) + Editable input (36px height)
  Fields: Product Name, SKU Code, Quantity, Unit Price, Supplier Name
  Each field shows original extracted value as placeholder

Confidence indicator (per field):
  High (>90%):   green dot
  Medium (70–90%): orange dot
  Low (<70%):    red dot + "Please verify" label (11px, red-600)

Actions:
  Reject → danger ghost button (radius-md, full-width, left)
  Confirm & Add to Inventory → primary pill button (full-width, right)

Audit note below buttons:
  "This action will be logged with your user ID and timestamp." (11px, ink-faint)
```

---

## 9. DATA VISUALIZATION

### Forecast chart (Recharts AreaChart)

```
Library: Recharts AreaChart
Container: white card, full-width, height 280px

Lines:
  Predicted demand: brand-600 (#0075DE), strokeWidth 2, smooth curve
  Actual sales:     ink-secondary (#31302E), strokeWidth 1.5, dashed
  Upper bound:      brand-100 (#D9E8FF), strokeWidth 1, dashed
  Lower bound:      brand-100 (#D9E8FF), strokeWidth 1, dashed

Area fill:
  Between upper/lower bounds: brand-50 (#EEF5FF), opacity 0.4

Reorder threshold line:
  orange-600 (#DD5B00), strokeWidth 1.5, dashed, labeled "Reorder point"

X axis: date, 12px, ink-faint, "DD MMM" format
Y axis: units, 12px, ink-faint, right-aligned numbers
Grid: horizontal only, hairline (#E6E6E6), 0.5px

Tooltip:
  White card, radius-md, Soft shadow
  Date (11px, ink-muted), Value (14px, 500, ink)

Legend: below chart, left-aligned, 12px, ink-muted
```

### Stock level indicator (inline in table)

```
Visual: horizontal bar, 120px wide, 6px height, radius-full
Background track: hairline

Fill color by level:
  >50% capacity:  green-200 (#A5D6A7)
  20–50%:         orange-100 (#FFCC80)
  <20%:           red-200 (#EF9A9A)
  0%:             red-600 (#E53935), pulsing animation

Text alongside bar: "247 / 500 units" (12px, tabular-nums, ink-secondary)
```

---

## 10. ICONOGRAPHY

**Library:** Lucide React (outline style only)
**Sizes:** 16px (inline with text), 18px (navigation), 20px (action buttons), 24px (empty states)
**Color:** inherits from parent text color. Never use a different color for icons than their paired text.
**Decorative icons:** `aria-hidden="true"`
**Meaningful icons:** `aria-label="descriptive text"`

### Key icon assignments

```
Dashboard overview  →  layout-dashboard
Inventory / stock   →  package
Forecasting         →  chart-line
Purchase orders     →  shopping-cart
AI assistant        →  bot (use purple-600 color)
Invoice scanning    →  scan
Suppliers           →  building-store
Audit log           →  clipboard-list
Settings            →  settings
User / profile      →  user-circle
Notifications       →  bell
Low stock alert     →  alert-triangle (orange-600)
Stockout critical   →  alert-octagon (red-600)
AI generated badge  →  sparkles (purple-600)
Confirmed / success →  circle-check (green-600)
Rejected            →  circle-x (red-600)
Approve action      →  check (green-600)
Reject action       →  x (red-600)
Edit                →  pencil
Export              →  download
Search              →  search
Filter              →  filter
Microphone          →  microphone (red-600 when recording)
Upload invoice      →  upload
PO document         →  file-text
Email sent          →  send
```

---

## 11. PAGE-BY-PAGE LAYOUT SPECS

### Dashboard home

```
Title: "Dashboard" (22px, 700, -0.25px tracking)
Subtitle: "Good morning, [Name]. You have 8 pending POs." (14px, ink-secondary)

Row 1: Stat cards grid (4 columns, gap 24px)
  - Total SKUs
  - Low Stock Alerts (orange accent)
  - Pending PO Approvals (orange accent)
  - Forecast Accuracy % (purple accent)

Row 2: 2-column grid (2fr + 1fr)
  Left:  30-day demand forecast chart (ForecastChart)
  Right: Reorder alert list (scrollable, orange/red badges)

Row 3: Full-width recent purchase orders table
  Columns: PO Number | Product | Supplier | Qty | Cost | Status | Date | Actions
```

### Inventory page

```
Title: "Inventory" (22px, 700, -0.25px tracking)
Header actions: "Export CSV" (utility button) + "Add Product" (primary pill)

Filter row below header:
  Search input (full text) + Category dropdown + Status dropdown + Stock level filter

Full-width data table:
  SKU | Product name | Category | Stock level (bar) | On Hand | Reserved | Reorder point | Supplier | Actions

Actions column (on row hover): Edit icon + Adjust stock icon
Selected row actions bar (top of table when rows selected): "Bulk export" + "Archive selected"
```

### PO Approval / Purchasing page

```
Two-column layout (1fr + 1fr):
  Left: "Pending Approval" list
    Each item: compact card, product name + qty + supplier + "AI Generated" badge
    Click to expand → right panel

  Right: Full POApprovalCard component
    (see component spec 8.8 above)

Below both columns: "PO History" full-width table
  Columns: PO # | Product | Supplier | Qty | Total | Status | Created | Approved by | Actions
```

### AI Assistant page

```
Split layout (3fr + 2fr):
  Left: ChatPanel (full height, see component 8.9)
  Right: Context panel
    "Current inventory snapshot" — top 5 low stock items
    "Recent queries" — last 5 NL queries run
    "Data sources" — list of RAG documents indexed
```

---

## 12. MOTION & ANIMATION

Keep animations minimal and purposeful. This is a productivity tool, not a marketing site.

```
Default transition: 150ms ease-out
Button press:       scale(0.9) transform, 100ms ease (Notion's signature press feedback)
Sidebar expand/collapse: width 200ms ease
Modal open: scale(0.96)→scale(1) + opacity 0→1, 150ms
Toast notifications: translateY(-8px)→0 + opacity 0→1, 200ms
Skeleton pulse: opacity 0.5→1→0.5, 1.5s infinite
Loading spinner: rotate 360deg, 700ms linear infinite
Chart animation: on mount only, 400ms ease-out
Mic recording pulse: scale(1)→scale(1.1)→scale(1), 1s infinite (red-600)

Reduced motion: wrap ALL animations in @media (prefers-reduced-motion: no-preference)
```

---

## 13. EMPTY STATES

Every list, table, and data view needs an empty state design.

```
Structure (centered in container):
  Icon (48px, ink-faint)
  Heading (15px, 500, ink-secondary)
  Body (14px, ink-muted, max-width 280px, centered)
  Action button (optional, primary pill variant)

Examples:
  No products:     📦 "No products yet"  "Add your first product to start tracking inventory."  [Add Product]
  No low stock:    ✅ "All stock levels are healthy"  "No items are below their reorder point."
  No pending POs:  🛒 "No POs awaiting approval"  "The AI will draft purchase orders when stock runs low."
  No AI queries:   🤖 "Ask anything about your inventory"  "Try: 'Show me slow-moving items this month'"
```

---

## 14. ACCESSIBILITY REQUIREMENTS

```
Color contrast:  All text ≥ 4.5:1 against background (WCAG AA)
Focus indicators: 3px ring, brand-100 color, on ALL interactive elements
Keyboard nav:    Full Tab navigation. No mouse-only interactions.
Screen readers:  aria-label on icon-only buttons. aria-live on dynamic content.
                 sr-only text on charts providing table summary alternative.
Form errors:     aria-describedby linking input to error message below it.
Loading states:  aria-busy="true" on loading regions. aria-live="polite" for updates.
Modals:          Focus trapped inside. Esc closes. Return focus on close.
Tables:          <th> with scope attribute. Caption element on all tables.
```

---

## 15. DARK MODE

All components must support dark mode via CSS class `.dark` on `<html>`.

```
Dark mode token overrides:
  Page background:   #1A1A1A (near-black, warm)
  Card background:   #2C2C2A (dark surface)
  Sidebar:           #1A1A1A with #2C2C2A active item
  Border color:      #444441 (dark hairline)
  Body text:         canvas-soft (#F6F5F4)
  Secondary text:    ink-faint (#A39E98)
  Heading text:      white (#FFFFFF)
  Input background:  #2C2C2A
  Table row hover:   #333330

Color ramps in dark mode (same semantic meanings, inverted fills):
  Success:   green-800 bg,  green-50 text
  Warning:   orange-800 bg,  orange-50 text
  Danger:    red-800 bg,    red-50 text
  Brand:     brand-800 bg,  brand-50 text
  AI/purple: purple-800 bg, purple-50 text
```

---

## 16. SAMPLE PROMPT FOR FIGMA AI / GALILEO AI

Copy and paste the following as your generation prompt:

---

**PROMPT TO COPY:**

```
Design a professional B2B SaaS dashboard called "SmartStock AI" for warehouse inventory management.

STYLE: Warm paper-calm aesthetic inspired by Notion. Clean, data-dense, desktop-first. White card surfaces on a warm off-white (#F6F5F4) page background. Hairline borders (#E6E6E6). Minimal elevation via layered micro-shadows — no heavy drop shadows.

COLORS:
- Primary CTA: #0075DE (Notion blue) for buttons and active states — pill-shaped CTAs
- Success: #1AAE39 (green) for in-stock and confirmed
- Warning: #DD5B00 (orange) for low stock and pending
- Danger: #E53935 (red) for stockouts and critical alerts
- AI/Forecasting: #D6B6F6 (purple) for all AI-generated content
- Neutral: #F6F5F4 (warm canvas) to #000000 (ink for headings)

TYPOGRAPHY: Inter (system-ui fallback), 22px page headings with -0.25px tracking, 15px card titles, 14px body, 12px captions. Sentence case everywhere. Weight 700 for headings, 400 for body. Tabular figures in tables.

LAYOUT: Left sidebar (56px collapsed, 220px expanded) + sticky 40px header + main content area. 4-column stat card grid at top. Charts and tables below.

BUTTON STYLES: Primary CTAs are pill-shaped (fully rounded). Secondary buttons use white bg with hairline border and soft layered shadow. Utility buttons use tighter 8px radius. All buttons get a scale(0.9) press transform on click.

COMPONENTS NEEDED:
1. Sidebar with icons for: Dashboard, Inventory, Forecasting, Purchasing, AI Assistant, Invoice Scan, Settings
2. Header with breadcrumb and user avatar + role badge
3. 4 stat cards: Total SKUs, Low Stock Alerts (orange), Pending POs (orange), Forecast Accuracy (purple)
4. 30-day demand forecast area chart (brand-blue line + orange dashed reorder threshold)
5. Reorder alert list (right of chart, orange/red status badges)
6. Data table: SKU | Product | Stock Level (bar indicator) | On Hand | Status | Actions
7. PO Approval Card with AI Generated badge (purple), product details, editable quantity, Approve/Reject buttons

STATUS BADGES (pill style, fully rounded, 11px, weight 600, uppercase):
- "In Stock" → green-50 bg, green-800 text
- "Low Stock" → orange-50 bg, orange-800 text
- "Out of Stock" → red-50 bg, red-800 text
- "AI Generated" → purple-50 bg, purple-800 text, sparkle icon

SPACING: 8px base unit. Cards: 24px padding. Grid gaps: 24px. Page margin: 32px.

ICONS: Lucide React outline style, 18px for navigation, 16px inline.

ACCESSIBILITY: All interactive elements need visible focus rings (3px, brand-100 color #D9E8FF). Sufficient contrast on all text.

DO NOT use: gradients, heavy drop shadows, decorative illustrations in the chrome, playful fonts, or consumer-app aesthetics. This is a professional operations tool.
```

---

_This document is the design source of truth for SmartStock AI._
_Version 2.0 — June 2026 — React-ive ITIIANS_
