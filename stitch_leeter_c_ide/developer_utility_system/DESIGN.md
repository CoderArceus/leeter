---
name: Developer Utility System
colors:
  surface: '#141313'
  surface-dim: '#141313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353434'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c7c8'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c6c6c7'
  primary: '#ffffff'
  on-primary: '#2f3131'
  primary-container: '#e2e2e2'
  on-primary-container: '#636565'
  inverse-primary: '#5d5f5f'
  secondary: '#c6c5cf'
  on-secondary: '#2f3038'
  secondary-container: '#4a4b53'
  on-secondary-container: '#bcbbc5'
  tertiary: '#ffffff'
  on-tertiary: '#2f3131'
  tertiary-container: '#e2e2e2'
  on-tertiary-container: '#636565'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e2'
  primary-fixed-dim: '#c6c6c7'
  on-primary-fixed: '#1a1c1c'
  on-primary-fixed-variant: '#454747'
  secondary-fixed: '#e3e1ec'
  secondary-fixed-dim: '#c6c5cf'
  on-secondary-fixed: '#1a1b22'
  on-secondary-fixed-variant: '#46464e'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#141313'
  on-background: '#e5e2e1'
  surface-variant: '#353434'
typography:
  display:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
spacing:
  unit: 4px
  sidebar-width: 240px
  panel-header-height: 36px
  gutter: 12px
  margin-sm: 8px
  margin-md: 16px
---

## Brand & Style
This design system is engineered for high-performance developer environments where speed, precision, and information density are paramount. The aesthetic follows a **Modern-Brutalist Utility** direction—stripping away visual noise like gradients and soft shadows in favor of structural integrity and clear boundaries.

The brand personality is clinical, reliable, and tool-like. It targets power users who prioritize keyboard-driven workflows and low-latency feedback. The UI should evoke a sense of focused "flow state," resembling a high-end physical instrument or a well-configured terminal emulator.

## Colors
This design system operates exclusively in a **Strict Dark Mode**. The palette is monochromatic, rooted in deep Zinc and Slate tones to minimize eye strain during long sessions.

- **Backgrounds:** Use `#09090B` for the base layer (editor/terminal) and `#18181B` for elevated surfaces like sidebars or panels.
- **Accents:** High-contrast White (`#FFFFFF`) is reserved for primary actions and active states.
- **Borders:** A consistent `#27272A` (Zinc-800) is used to define all structural boundaries.
- **Status:** Saturated but functional colors (Emerald, Rose, Amber) are used sparingly only to denote system status or code health.

## Typography
The system utilizes a dual-font strategy. **Geist** provides a geometric, neutral foundation for UI elements, navigation, and inputs. **JetBrains Mono** is used for all technical content, including code editors, logs, data tables, and metadata labels.

- **Scale:** Maintain a tight scale. Most UI text should live between 12px and 14px to maximize screen real estate.
- **Hierarchy:** Use font weight (Medium/SemiBold) and color opacity (Zinc-400 vs Zinc-100) rather than large size jumps to indicate importance.
- **Monospace:** Use JetBrains Mono for any numerical data or IDs to ensure perfect vertical alignment in lists and trees.

## Layout & Spacing
The layout is a **Modular Panel System**. Content is divided into functional zones (Sidebar, Editor, Console, Inspector) separated by 1px borders.

- **Rhythm:** Based on a 4px grid. Standard padding for interactive elements is 8px horizontal, 4px vertical.
- **Density:** Information density is high. Standard row heights for trees and lists are fixed at 28px or 32px.
- **Responsive:** On smaller screens, sidebars collapse into icons. The "Main Editor" area is fluid, while utility panels have fixed minimum widths (e.g., 240px).

## Elevation & Depth
Depth is communicated through **Tonal Layering** and **High-Contrast Outlines** rather than shadows.

- **Tiers:** 
  - Level 0: `#09090B` (Canvas/Editor)
  - Level 1: `#18181B` (Sidebars/Modals)
  - Level 2: `#27272A` (Hover states/Selected items)
- **Borders:** Every container must have a 1px solid border (`#27272A`).
- **Active State:** Use a 1px solid white border or a 2px left-accent bar to indicate the focused panel. Avoid any glow or blur effects.

## Shapes
The system uses a **Strict Sharp** aesthetic. 

- **Corners:** 0px radius for all primary containers, tabs, and terminal panels. 
- **Small Elements:** For buttons or inputs, a maximum radius of 2px (`rounded-sm`) may be used only if necessary to distinguish them from the background, but 0px is preferred for the "utility" feel.
- **Tabs:** Use a "Folder" or "Slanted" tab style with 0px corners, where the active tab is identified by a top-border highlight.

## Components

### Buttons & Action Groups
- **Primary:** Solid White background with Black text. 0px radius.
- **Secondary:** Outline style with `#27272A` border. No background fill unless hovered.
- **Action Groups:** Flush buttons joined together with 1px borders between them, forming a single visual unit.

### Tabbed Interface
- Tabs are 36px high. Active tabs have a background of `#18181B` and a subtle 2px top border in White. Inactive tabs have no background and Zinc-500 text.

### Data Trees & Debugger
- 28px row height. Use 1px dotted lines for indentation guides.
- Chevron icons for expansion. Use JetBrains Mono for keys and values.
- Syntax highlighting should follow a "Subdued" theme (e.g., dim greens for strings, dim blues for keywords).

### Terminal & Logs
- Background: `#09090B`. 
- Prefix every line with a timestamp or log level in a muted color.
- Errors should highlight the entire line background with a 10% opacity Rose tint.

### Inputs & Fields
- Dark background (`#09090B`) with a 1px Zinc-800 border. 
- Focus state: Border color changes to White. No "glow" or "ring" offset.

### Progress Bars
- 4px height. Track color: `#27272A`. Fill color: White or Emerald. No animation unless active/loading.