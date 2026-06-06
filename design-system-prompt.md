# SmartStock AI — Design System Prompt

# For use with Figma AI, Galileo AI, Uizard, Locofy, or any AI design tool

---

## PROJECT CONTEXT

You are designing **SmartStock AI**, a B2B SaaS warehouse inventory management dashboard for warehouse managers and procurement teams at medium-to-large e-commerce businesses. The product is desktop-first, data-dense, and used daily by non-technical operations staff. The UI must feel professional, trustworthy, and efficient — closer to Linear or Notion than to a consumer app. Avoid decorative elements, gradients, and anything that prioritises aesthetics over readability.

---

## 1. BRAND IDENTITY

**Product name:** SmartStock AI
**Tagline:** Proactive demand planning — know what you need before you run out.
**Personality:** Confident, precise, intelligent, calm under pressure.
**Tone:** Professional but not cold. Clear, direct, data-forward.
**Primary audience:** Warehouse managers, 25–50 years old, desktop-only, working in fast-paced logistics environments.

---

## 2. COLOR SYSTEM

### Primary — Brand Blue (actions, links, buttons, focus rings)

| Token     | Hex     | Usage                             |
| --------- | ------- | --------------------------------- |
| brand-50  | #E6F1FB | Button hover bg, info backgrounds |
| brand-100 | #B5D4F4 | Borders on info cards             |
| brand-400 | #378ADD | Hover states                      |
| brand-600 | #185FA5 | Primary buttons, active nav items |
| brand-800 | #0C447C | Text on brand-50 backgrounds      |
| brand-900 | #042C53 | Darkest text on light brand fills |

### Success — Green (in-stock, confirmed, approved)

| Token     | Hex     | Usage                    |
| --------- | ------- | ------------------------ |
| green-50  | #EAF3DE | Success background fills |
| green-200 | #97C459 | Success borders          |
| green-600 | #3B6D11 | Success badge text       |
| green-800 | #27500A | Text on green-50         |

### Warning — Amber (low stock, pending approval, reorder alert)

| Token     | Hex     | Usage                       |
| --------- | ------- | --------------------------- |
| amber-50  | #FAEEDA | Warning background fills    |
| amber-100 | #FAC775 | Warning borders, icon fills |
| amber-600 | #854F0B | Warning badge text          |
| amber-800 | #633806 | Text on amber-50            |

### Danger — Red (stockout, rejected, critical alert)

| Token   | Hex     | Usage                   |
| ------- | ------- | ----------------------- |
| red-50  | #FCEBEB | Danger background fills |
| red-200 | #F09595 | Danger borders          |
| red-600 | #A32D2D | Danger badge text       |
| red-800 | #791F1F | Text on red-50          |

### AI / Forecasting — Purple (AI-generated content, forecast data, agent actions)

| Token      | Hex     | Usage                          |
| ---------- | ------- | ------------------------------ |
| purple-50  | #EEEDFE | AI feature backgrounds         |
| purple-100 | #CECBF6 | AI borders                     |
| purple-600 | #534AB7 | AI badge text, forecast labels |
| purple-800 | #3C3489 | Text on purple-50              |

### Neutral — Gray (structure, borders, disabled states)

| Token    | Hex     | Usage                    |
| -------- | ------- | ------------------------ |
| gray-50  | #F1EFE8 | Page background          |
| gray-100 | #D3D1C7 | Disabled fills, dividers |
| gray-400 | #888780 | Placeholder text         |
| gray-600 | #5F5E5A | Secondary text           |
| gray-800 | #444441 | Primary text (dark)      |
| gray-900 | #2C2C2A | Headings                 |

### Semantic color rules

- **Never use color alone** to convey status — always pair with an icon or text label.
- **AI-generated content** always uses purple tokens. Users learn: purple = AI.
- **Text on colored backgrounds** must always use the 800 stop of that same ramp.
- **Contrast ratio:** all text/background pairs must meet 4.5:1 minimum (WCAG AA).

---

## 3. TYPOGRAPHY

### Font stack

- **Primary:** System UI stack — `"Segoe UI", system-ui, -apple-system, sans-serif`
- **Monospace:** `"Cascadia Code", "Fira Code", "Courier New", monospace` — used for SKU codes, PO numbers, API keys

### Type scale

| Role            | Size | Weight | Line Height | Usage                             |
| --------------- | ---- | ------ | ----------- | --------------------------------- |
| Page heading    | 22px | 500    | 1.2         | Dashboard page titles             |
| Section heading | 18px | 500    | 1.3         | Card headings, section titles     |
| Card title      | 15px | 500    | 1.4         | Table headers, panel titles       |
| Body            | 13px | 400    | 1.6         | All body copy, table cell data    |
| Caption         | 11px | 400    | 1.5         | Timestamps, metadata, helper text |
| Monospace       | 12px | 400    | 1.5         | SKU codes, PO numbers, IDs        |

### Typography rules

- Use **sentence case** everywhere. Never ALL CAPS or Title Case in UI.
- Numbers in tables and stat cards use **tabular figures** (font-variant-numeric: tabular-nums) so columns align.
- Truncate long text with ellipsis (...) — never wrap text inside table cells.
- Minimum font size: **11px**. Never smaller.

---

## 4. SPACING SYSTEM

Base unit: **4px**. All spacing is a multiple of 4.

| Token    | Value | Common usage                             |
| -------- | ----- | ---------------------------------------- |
| space-1  | 4px   | Icon to label gap                        |
| space-2  | 8px   | Badge internal padding, tight row gap    |
| space-3  | 12px  | Input internal padding, compact card gap |
| space-4  | 16px  | Default component gap                    |
| space-5  | 20px  | Card internal padding                    |
| space-6  | 24px  | Section gap, grid gap                    |
| space-8  | 32px  | Page horizontal margin                   |
| space-10 | 40px  | Section vertical gap                     |
| space-12 | 48px  | Page vertical spacing                    |

---

## 5. BORDER RADIUS

| Token       | Value  | Usage                           |
| ----------- | ------ | ------------------------------- |
| radius-sm   | 4px    | Badges, pills, small tags       |
| radius-md   | 6px    | Inputs, buttons, small cards    |
| radius-lg   | 10px   | Main cards, modals, panels      |
| radius-xl   | 16px   | Large feature cards             |
| radius-full | 9999px | Avatar circles, toggle switches |

---

## 6. SHADOWS & ELEVATION

**No decorative shadows.** Elevation is communicated through borders and background contrast, not drop shadows.

| Level      | Style                         | Usage                             |
| ---------- | ----------------------------- | --------------------------------- |
| Flat       | No shadow, border: 0.5px      | Cards, table rows                 |
| Raised     | `0 1px 3px rgba(0,0,0,0.08)`  | Dropdowns, tooltips               |
| Modal      | `0 4px 24px rgba(0,0,0,0.12)` | Modal dialogs only                |
| Focus ring | `0 0 0 3px #B5D4F4`           | All interactive elements on focus |

---

## 7. LAYOUT & GRID

### App shell structure

```
┌─────────────────────────────────────────────────────┐
│                    Header (40px)                    │
├──────────┬──────────────────────────────────────────┤
│ Sidebar  │                                          │
│ 56px     │          Main Content Area               │
│(collapsed)│         (flex-1, scrollable)            │
│ 220px    │                                          │
│(expanded) │                                         │
└──────────┴──────────────────────────────────────────┘
```

### Sidebar

- Collapsed: **56px wide** — shows icons only
- Expanded: **220px wide** — shows icons + labels
- Transition: `width 200ms ease`
- Background: white with right border `1px solid gray-100`
- Active nav item: `background: brand-50, color: brand-600, border-left: 2px solid brand-600`

### Header

- Height: **40px** (compact — data-heavy tools use space efficiently)
- Background: white, bottom border `1px solid gray-100`
- Contains: breadcrumb left, user avatar + role badge right
- Sticky `top: 0, z-index: 10`

### Content grid

- Page max-width: **1440px**, centered
- Page horizontal padding: **32px** (`px-8`)
- Stat card row: `grid, 4 columns, gap: 24px`
- Chart + side panel: `grid, 2fr + 1fr, gap: 24px`
- Full-width table: `100% width`

### Breakpoints

| Name | Width  | Behavior                         |
| ---- | ------ | -------------------------------- |
| sm   | 640px  | 1-column grid, sidebar hidden    |
| md   | 768px  | 2-column grid, sidebar icon-only |
| lg   | 1024px | Full layout (primary target)     |
| xl   | 1280px | Wider content, larger charts     |
| 2xl  | 1536px | Centered max-width content       |

---

## 8. COMPONENTS

### 8.1 Button

```
Variants: primary | secondary | danger | ghost
Sizes: sm (28px height) | md (36px height) | lg (44px height)

Primary:   bg brand-600, text white, hover bg brand-800
Secondary: bg white, border brand-600, text brand-600, hover bg brand-50
Danger:    bg red-600, text white, hover bg red-800
Ghost:     no bg, no border, text brand-600, hover bg brand-50
Disabled:  bg gray-100, text gray-400, cursor not-allowed

Border radius: radius-md (6px)
Font: 13px, weight 500
Padding: sm (px-3 py-1.5) | md (px-4 py-2) | lg (px-5 py-2.5)
Focus ring: 0 0 0 3px brand-100
```

### 8.2 Badge / Status pill

```
Sizes: small only (inline with text)
Border radius: radius-sm (4px)
Font: 11px, weight 500
Padding: px-2 py-0.5

Status mappings:
  "In Stock"         → bg green-50,  text green-800,  dot green-600
  "Low Stock"        → bg amber-50,  text amber-800,  dot amber-600
  "Out of Stock"     → bg red-50,    text red-800,    dot red-600
  "Draft"            → bg gray-100,  text gray-600
  "Pending Approval" → bg amber-50,  text amber-800
  "Approved"         → bg green-50,  text green-800
  "Sent"             → bg brand-50,  text brand-800
  "Confirmed"        → bg green-50,  text green-800
  "Rejected"         → bg red-50,    text red-800
  "AI Generated"     → bg purple-50, text purple-800, sparkle icon
  "Viewer"           → bg gray-100,  text gray-600
  "Manager"          → bg brand-50,  text brand-800
  "Admin"            → bg purple-50, text purple-800
```

### 8.3 Input field

```
Height: 36px
Border: 0.5px solid gray-100, radius-md
Background: white
Font: 13px, text gray-900
Placeholder: gray-400

States:
  Default: border gray-100
  Hover:   border gray-400
  Focus:   border brand-600, ring 0 0 0 3px brand-100
  Error:   border red-600, ring 0 0 0 3px red-50
  Disabled: bg gray-50, text gray-400

With label (FormField molecule):
  Label above: 11px, gray-600, mb-1
  Error below: 11px, red-600, mt-1, with warning icon
```

### 8.4 Stat card

```
Background: gray-50 (surface card, not raised)
Border radius: radius-md
Padding: 16px
Height: fixed 96px (no layout shift on load)
Min-width: 160px

Structure:
  ↳ Label (11px, gray-600, uppercase, letter-spacing 0.05em)
  ↳ Value (24px, weight 500, gray-900) — uses tabular-nums
  ↳ Trend indicator (11px): ↑ green-600 or ↓ red-600 + percentage
  ↳ Skeleton on load: matches exact dimensions (gray-100 animated pulse)

Example cards for SmartStock AI:
  "Total SKUs"         value: 1,247        trend: none
  "Low Stock Alerts"   value: 23           trend: ↑ 12% (amber-600)
  "Pending POs"        value: 8            trend: none
  "Forecast Accuracy"  value: 87.4%        trend: ↑ 2.1% (green-600)
```

### 8.5 Data table

```
Table layout: fixed (prevents layout shift on load)
Row height: 44px (single-line data rows)
Header height: 36px

Header row:
  bg gray-50, border-bottom 1px gray-100
  font: 11px, weight 500, gray-600, uppercase, letter-spacing 0.05em

Data rows:
  bg white, border-bottom 0.5px gray-100
  hover: bg gray-50
  selected: bg brand-50, border-left 2px brand-600

Column types:
  SKU code → monospace 12px, gray-600
  Product name → 13px, gray-900, truncate with tooltip
  Number / quantity → tabular-nums, right-aligned
  Status → inline Badge component
  Date → 12px, gray-600, "DD MMM YYYY" format
  Actions → ghost icon buttons, visible on row hover only

Pagination:
  Below table, right-aligned
  "Showing 1–20 of 1,247 results" (13px, gray-600)
  Prev / Next buttons (secondary variant)
  Page size selector: 20 / 50 / 100 rows
```

### 8.6 Card

```
Background: white
Border: 0.5px solid gray-100
Border radius: radius-lg (10px)
Padding: 20px
Box shadow: none (flat — uses border only)

Card header:
  Title: 15px, weight 500, gray-900
  Subtitle (optional): 11px, gray-600
  Action (optional): ghost button or icon, right-aligned
  Border-bottom: 0.5px gray-100, pb-4 mb-4

Card sections:
  Divider between sections: 0.5px gray-100, my-4
```

### 8.7 Sidebar navigation

```
Item height: 40px
Padding: px-3
Border radius: radius-md
Font: 13px

States:
  Default:  text gray-600, icon gray-400
  Hover:    bg gray-50, text gray-900, icon gray-600
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

Card style: white, border-left 3px solid amber-600, radius-lg, shadow modal
Header: "Purchase Order Draft" (15px, 500) + "AI Generated" badge (purple)

Content rows (label + value pairs, 44px each):
  SKU            monospace 12px
  Product        13px, gray-900
  Predicted stockout  12px, red-600, with calendar icon
  Recommended qty     16px, 500, gray-900 (editable input field)
  Supplier       13px, gray-600
  Estimated cost 16px, 500, gray-900

Reasoning trace (collapsible):
  "Why did the AI flag this?" accordion
  Body: 12px, gray-600, italic, bg purple-50, border-left 2px purple-100, p-3

Actions (bottom of card, full-width):
  Reject   → danger ghost button
  Edit Qty → secondary button
  Approve  → primary button (green-600 variant for approval)
```

### 8.9 Chat panel (AI Assistant)

```
Container: white card, full-height, flex-col
Height: fills viewport minus header + sidebar

Message bubbles:
  User:  right-aligned, bg brand-600, text white, radius-lg radius-br-sm
  AI:    left-aligned, bg gray-50, text gray-900, radius-lg radius-bl-sm
  Font:  13px, line-height 1.6

Citation tags (inline within AI messages):
  Style: bg purple-50, text purple-800, border 0.5px purple-100
  Format: "[Source: supplier_policy.pdf, Page: 3]"
  Font: 11px, monospace

Input area (bottom of panel):
  Height: 52px
  Input: full-width, 36px height, radius-full
  Right icons: microphone button (voice) + send button
  Mic active state: red-600 icon with pulse animation

Loading state (AI thinking):
  Three-dot animation in AI message bubble
  bg gray-50, dots gray-400
```

### 8.10 Invoice confirmation card

```
Triggered after GPT-4o Vision extracts data from uploaded invoice.

Layout: 2-column grid
  Left col (50%):  uploaded invoice image (contained, max-h 400px)
  Right col (50%): extracted fields (editable)

Extracted field rows:
  Label (11px, gray-600) + Editable input (36px height)
  Fields: Product Name, SKU Code, Quantity, Unit Price, Supplier Name
  Each field shows original extracted value as placeholder

Confidence indicator (per field):
  High (>90%):   green dot
  Medium (70–90%): amber dot
  Low (<70%):    red dot + "Please verify" label (11px, red-600)

Actions:
  Reject → danger secondary button (full-width, left)
  Confirm & Add to Inventory → primary button (full-width, right)

Audit note below buttons:
  "This action will be logged with your user ID and timestamp." (11px, gray-400)
```

---

## 9. DATA VISUALIZATION

### Forecast chart (Recharts AreaChart)

```
Library: Recharts AreaChart
Container: white card, full-width, height 280px

Lines:
  Predicted demand: brand-600 (#185FA5), strokeWidth 2, smooth curve
  Actual sales:     gray-600 (#5F5E5A), strokeWidth 1.5, dashed
  Upper bound:      brand-100 (#B5D4F4), strokeWidth 1, dashed (confidence interval)
  Lower bound:      brand-100 (#B5D4F4), strokeWidth 1, dashed (confidence interval)

Area fill:
  Between upper/lower bounds: brand-50 (#E6F1FB), opacity 0.4

Reorder threshold line:
  amber-600 (#854F0B), strokeWidth 1.5, dashed, labeled "Reorder point"

X axis: date, 12px, gray-400, "DD MMM" format
Y axis: units, 12px, gray-400, right-aligned numbers
Grid: horizontal only, gray-100 (#D3D1C7), 0.5px

Tooltip:
  White card, radius-md, shadow raised
  Date (11px, gray-600), Value (13px, 500, gray-900)

Legend: below chart, left-aligned, 11px, gray-600
```

### Stock level indicator (inline in table)

```
Visual: horizontal bar, 120px wide, 6px height, radius-full
Background track: gray-100

Fill color by level:
  >50% capacity:  green-200 (#97C459)
  20–50%:         amber-100 (#FAC775)
  <20%:           red-200 (#F09595)
  0%:             red-600 (#A32D2D), pulsing animation

Text alongside bar: "247 / 500 units" (12px, tabular-nums, gray-600)
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
Low stock alert     →  alert-triangle (amber-600)
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
Title: "Dashboard" (22px, 500)
Subtitle: "Good morning, [Name]. You have 8 pending POs." (13px, gray-600)

Row 1: Stat cards grid (4 columns, gap 24px)
  - Total SKUs
  - Low Stock Alerts (amber accent)
  - Pending PO Approvals (amber accent)
  - Forecast Accuracy % (purple accent)

Row 2: 2-column grid (2fr + 1fr)
  Left:  30-day demand forecast chart (ForecastChart)
  Right: Reorder alert list (scrollable, amber/red badges)

Row 3: Full-width recent purchase orders table
  Columns: PO Number | Product | Supplier | Qty | Cost | Status | Date | Actions
```

### Inventory page

```
Title: "Inventory" (22px, 500)
Header actions: "Export CSV" (ghost button) + "Add Product" (primary button)

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
  Icon (48px, gray-300)
  Heading (15px, 500, gray-700)
  Body (13px, gray-500, max-width 280px, centered)
  Action button (optional, primary variant)

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
  Page background:   gray-900 (#2C2C2A)
  Card background:   gray-800 (#444441)
  Sidebar:           gray-900 with gray-800 active item
  Border color:      gray-700 (0.5px)
  Body text:         gray-100 (#D3D1C7)
  Secondary text:    gray-400 (#888780)
  Heading text:      white (#FFFFFF)
  Input background:  gray-800
  Table row hover:   gray-700

Color ramps in dark mode (same semantic meanings, inverted fills):
  Success:   green-800 bg,  green-100 text
  Warning:   amber-800 bg,  amber-100 text
  Danger:    red-800 bg,    red-100 text
  Brand:     brand-800 bg,  brand-100 text
  AI/purple: purple-800 bg, purple-100 text
```

---

## 16. SAMPLE PROMPT FOR FIGMA AI / GALILEO AI

Copy and paste the following as your generation prompt:

---

**PROMPT TO COPY:**

```
Design a professional B2B SaaS dashboard called "SmartStock AI" for warehouse inventory management.

STYLE: Clean, data-dense, desktop-first. Similar to Linear or Notion. No decorative gradients or drop shadows. Flat card design with 0.5px borders. White backgrounds with gray-50 page background.

COLORS:
- Primary: #185FA5 (brand blue) for buttons and active states
- Success: #3B6D11 (green) for in-stock and confirmed
- Warning: #854F0B (amber) for low stock and pending
- Danger: #A32D2D (red) for stockouts and critical alerts
- AI/Forecasting: #534AB7 (purple) for all AI-generated content
- Neutral: gray scale from #F1EFE8 (bg) to #2C2C2A (text)

TYPOGRAPHY: System UI, 22px page titles, 15px card titles, 13px body, 11px captions. Sentence case everywhere. Tabular numbers in tables.

LAYOUT: Left sidebar (56px collapsed, 220px expanded) + sticky 40px header + main content area. 4-column stat card grid at top. Charts and tables below.

COMPONENTS NEEDED:
1. Sidebar with icons for: Dashboard, Inventory, Forecasting, Purchasing, AI Assistant, Invoice Scan, Settings
2. Header with breadcrumb and user avatar + role badge
3. 4 stat cards: Total SKUs, Low Stock Alerts (amber), Pending POs (amber), Forecast Accuracy (purple)
4. 30-day demand forecast area chart (brand-blue line + amber dashed reorder threshold)
5. Reorder alert list (right of chart, amber/red status badges)
6. Data table: SKU | Product | Stock Level (bar indicator) | On Hand | Status | Actions
7. PO Approval Card with AI Generated badge (purple), product details, editable quantity, Approve/Reject buttons

STATUS BADGES (pill style, 11px, 4px radius):
- "In Stock" → green-50 bg, green-800 text
- "Low Stock" → amber-50 bg, amber-800 text
- "Out of Stock" → red-50 bg, red-800 text
- "AI Generated" → purple-50 bg, purple-800 text, sparkle icon

SPACING: 4px base unit. Cards: 20px padding. Grid gaps: 24px. Page margin: 32px.

ICONS: Lucide React outline style, 18px for navigation, 16px inline.

ACCESSIBILITY: All interactive elements need visible focus rings (3px, brand-100 color). Sufficient contrast on all text.

DO NOT use: gradients, drop shadows on cards, purple/teal gradient backgrounds, decorative illustrations, playful fonts, or consumer-app aesthetics. This is a professional operations tool.
```

---

_This document is the design source of truth for SmartStock AI._
_Version 1.0 — June 2025 — React-ive ITIIANS_
