---
name: neo-brutalism
description: Loads the complete neo-brutalism design system. Activates when the user chooses neo-brutalism style in frontend-craftsman mode. Contains the full component library, color system, typography, spacing, and interaction rules that must be applied consistently to every generated component.
---

When /neo-brutalism is activated, this design system becomes the law. Apply every rule to every component you generate. One component that breaks the system destroys the visual consistency of the whole interface.

## Core Philosophy

Neo-brutalism is raw, structural, and deliberately confrontational. Elements expose their construction — borders are thick, shadows are hard, nothing is softened or rounded. It looks intentional, not accidental. The aesthetic communicates that the interface is *built*, not *designed away*.

---

## Color System

**The full palette — use nothing else:**

| Token | Hex | Usage |
|-------|-----|-------|
| `brutal-black` | `#000000` | Borders, shadows, primary text |
| `brutal-white` | `#FFFFFF` | Component backgrounds, surfaces |
| `brutal-yellow` | `#FFFF00` | Primary CTA, active states, highlights |
| `brutal-red` | `#FF4444` | Errors, destructive actions, alerts |
| `brutal-teal` | `#00C9A7` | Secondary accent, success states |
| `brutal-bg` | `#F2F2F0` | Page background |
| `brutal-muted` | `#E8E8E8` | Disabled states, subtle dividers |

**Hard rules:**
- No gradients. Ever. Not even subtle ones.
- No opacity below 1.0 on UI elements (shadows are the only exception)
- No CSS named colors — always hex
- Text is always `#000000` on light backgrounds, always `#FFFFFF` on black backgrounds
- Never use gray for borders — only `#000000`

---

## Typography

**Font:** `'Space Grotesk'` from Google Fonts — load it. Fallback: `system-ui, sans-serif`.
**Mono font:** `'JetBrains Mono'` for code, data, and labels.

```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
```

| Element | Size | Weight | Transform | Letter-spacing |
|---------|------|--------|-----------|----------------|
| Page title | `3.5rem` | `800` | `uppercase` | `0.02em` |
| Section heading | `2rem` | `700` | none | none |
| Card heading | `1.25rem` | `700` | none | none |
| Body text | `1rem` | `500` | none | none |
| Button label | `0.875rem` | `700` | `uppercase` | `0.08em` |
| Small label | `0.75rem` | `700` | `uppercase` | `0.1em` |
| Data/number | `1rem` | `700` | none | none — use mono font |

Line heights: `1.1` for headings, `1.6` for body text.

---

## Borders

- **Default:** `2px solid #000000`
- **Cards and containers:** `3px solid #000000`
- **Inputs:** `2px solid #000000`, becomes `3px solid #000000` on focus
- **Border radius:** `0px` everywhere — no exceptions, no rounding
- **Dividers:** `2px solid #000000`

---

## Shadows — The Signature Element

Hard offset box-shadows with zero blur radius. This is what makes neo-brutalism instantly recognisable.

```css
/* Small — buttons, inputs, badges, chips */
box-shadow: 3px 3px 0px #000000;

/* Medium — cards, panels, dropdowns */
box-shadow: 5px 5px 0px #000000;

/* Large — modals, elevated containers */
box-shadow: 8px 8px 0px #000000;
```

**The press interaction** — elements simulate being pushed when hovered/active:
```css
/* Hover: element shifts toward its shadow */
.interactive:hover {
  transform: translate(3px, 3px);
  box-shadow: 0px 0px 0px #000000;
}

/* Active/pressed: same but faster */
.interactive:active {
  transform: translate(3px, 3px);
  box-shadow: 0px 0px 0px #000000;
}
```

Transition: `transform 75ms ease-out, box-shadow 75ms ease-out` — fast and snappy, never slow.

---

## Spacing

**8px base grid only.** Allowed values: `4, 8, 12, 16, 24, 32, 48, 64, 80, 96px`.
Never use `5px`, `7px`, `15px`, `20px`, or any value not on this grid.

---

## Tailwind Configuration

Add to `tailwind.config.js`:

```js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brutal: {
          black: '#000000',
          white: '#FFFFFF',
          yellow: '#FFFF00',
          red: '#FF4444',
          teal: '#00C9A7',
          bg: '#F2F2F0',
          muted: '#E8E8E8',
        },
      },
      boxShadow: {
        'brutal-sm': '3px 3px 0px #000000',
        'brutal-md': '5px 5px 0px #000000',
        'brutal-lg': '8px 8px 0px #000000',
        'brutal-none': '0px 0px 0px #000000',
      },
      borderWidth: {
        '3': '3px',
      },
    },
  },
}
```

---

## Component Patterns

### Button — Primary
```tsx
<button className="
  bg-brutal-yellow border-2 border-brutal-black
  px-6 py-3 font-sans font-bold text-sm uppercase tracking-widest text-brutal-black
  shadow-brutal-sm
  hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none
  active:translate-x-[3px] active:translate-y-[3px] active:shadow-brutal-none
  transition-all duration-75 cursor-pointer
">
  SUBMIT
</button>
```

### Button — Secondary
```tsx
<button className="
  bg-brutal-white border-2 border-brutal-black
  px-6 py-3 font-sans font-bold text-sm uppercase tracking-widest text-brutal-black
  shadow-brutal-sm
  hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none
  transition-all duration-75 cursor-pointer
">
  CANCEL
</button>
```

### Button — Destructive
```tsx
<button className="
  bg-brutal-red border-2 border-brutal-black
  px-6 py-3 font-sans font-bold text-sm uppercase tracking-widest text-brutal-black
  shadow-brutal-sm
  hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none
  transition-all duration-75 cursor-pointer
">
  DELETE
</button>
```

### Card
```tsx
<div className="bg-brutal-white border-3 border-brutal-black p-6 shadow-brutal-md">
  <h3 className="font-sans font-bold text-xl mb-4">CARD TITLE</h3>
  {/* content */}
</div>
```

### Input / Text Field
```tsx
<div className="flex flex-col gap-2">
  <label className="font-mono font-bold text-xs uppercase tracking-widest">
    FIELD LABEL
  </label>
  <input
    className="
      border-2 border-brutal-black bg-brutal-white
      px-4 py-3 font-sans font-medium text-base
      focus:outline-none focus:border-3 focus:shadow-brutal-sm
      transition-all duration-75
    "
    placeholder="..."
  />
</div>
```

### Badge / Status Tag
```tsx
// Default
<span className="bg-brutal-yellow border-2 border-brutal-black px-3 py-1 font-mono font-bold text-xs uppercase tracking-widest">
  ACTIVE
</span>

// Success
<span className="bg-brutal-teal border-2 border-brutal-black px-3 py-1 font-mono font-bold text-xs uppercase tracking-widest">
  DONE
</span>

// Error
<span className="bg-brutal-red border-2 border-brutal-black px-3 py-1 font-mono font-bold text-xs uppercase tracking-widest">
  FAILED
</span>
```

### Alert / Notification Panel
```tsx
// Error
<div className="bg-brutal-red border-3 border-brutal-black p-4 shadow-brutal-sm">
  <p className="font-sans font-bold text-sm uppercase tracking-wide">
    ⚠ ERROR: {message}
  </p>
</div>

// Info / Warning
<div className="bg-brutal-yellow border-3 border-brutal-black p-4 shadow-brutal-sm">
  <p className="font-sans font-bold text-sm uppercase tracking-wide">
    ● {message}
  </p>
</div>
```

### Data Metric Card (for dashboards)
```tsx
<div className="bg-brutal-white border-3 border-brutal-black p-6 shadow-brutal-md">
  <p className="font-mono font-bold text-xs uppercase tracking-widest text-brutal-black/60 mb-2">
    METRIC LABEL
  </p>
  <p className="font-sans font-black text-5xl text-brutal-black leading-none">
    {value}
  </p>
  <p className="font-mono text-xs text-brutal-black/60 mt-2 uppercase tracking-wide">
    {unit}
  </p>
</div>
```

### Navigation Bar
```tsx
<nav className="w-full bg-brutal-black border-b-3 border-brutal-black px-8 py-4 flex items-center justify-between">
  <span className="font-sans font-black text-xl uppercase tracking-widest text-brutal-yellow">
    APP NAME
  </span>
  <div className="flex gap-6">
    <a className="font-mono font-bold text-sm uppercase tracking-widest text-brutal-white hover:text-brutal-yellow transition-colors duration-75">
      NAV ITEM
    </a>
    {/* active state: */}
    <a className="font-mono font-bold text-sm uppercase tracking-widest text-brutal-yellow border-b-2 border-brutal-yellow">
      ACTIVE ITEM
    </a>
  </div>
</nav>
```

### Table
```tsx
<table className="w-full border-3 border-brutal-black">
  <thead className="bg-brutal-black text-brutal-white">
    <tr>
      <th className="border-r-2 border-brutal-white px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest text-left">
        COLUMN
      </th>
    </tr>
  </thead>
  <tbody>
    <tr className="border-b-2 border-brutal-black bg-brutal-white even:bg-brutal-muted">
      <td className="border-r-2 border-brutal-black px-4 py-3 font-sans text-sm">
        value
      </td>
    </tr>
  </tbody>
</table>
```

### Progress Bar
```tsx
<div className="w-full border-2 border-brutal-black bg-brutal-muted h-6">
  <div
    className="h-full bg-brutal-yellow border-r-2 border-brutal-black transition-all duration-300"
    style={{ width: `${percentage}%` }}
  />
</div>
```

---

## Layout Rules

- **Max content width:** `1280px`, centered with `mx-auto`
- **Page background:** always `bg-brutal-bg` (`#F2F2F0`)
- **Grid:** explicit CSS Grid with visible gaps (`gap-6` or `gap-8`)
- **Section padding:** minimum `px-8 py-12`
- **No floating elements** without borders and shadows
- **Dashboard layout:** sidebar left (`w-64 bg-brutal-black`) + main content right
- **Sidebar items:** full-width, `border-b-2 border-brutal-white/20`, active state with `bg-brutal-yellow` and black text

---

## Loading States

No skeleton loaders — use a brutal loading indicator:
```tsx
<div className="border-3 border-brutal-black border-t-brutal-yellow w-8 h-8 animate-spin" />
```
Or a simple text indicator:
```tsx
<span className="font-mono font-bold text-sm uppercase tracking-widest animate-pulse">
  LOADING...
</span>
```

---

## What NEVER to Do

- No gradients (linear, radial, conic — none)
- No `border-radius` anywhere — `rounded-none` on everything
- No soft box shadows (never use blur in box-shadow)
- No transitions longer than `150ms`
- No opacity hacks for color variation — use actual colors from the palette
- No ghost/outline buttons without hard shadows
- No icons floating without a bordered container
- No `text-gray-*` for anything visible — only `brutal-black` or `brutal-white`
- No animations beyond the press interaction and loading spinner
