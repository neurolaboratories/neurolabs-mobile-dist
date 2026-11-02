# Integration Guide PDF Generation Rules

This file defines the canonical rules for generating `Neurolabs-Android-Integration-Guide.pdf` from `Neurolabs-Android-Integration-Guide.md`.
Use these rules whenever regenerating guide PDFs.

## Source Of Truth
- Visual baseline: `neurolabs-cordova-sdk/contract/Neurolabs Cordova Plugin Interface Contract.pdf`
- Input file: `Neurolabs-Android-Integration-Guide.md` (repo root)
- Output file: `Neurolabs-Android-Integration-Guide.pdf` (repo root)

## Layout
- Page size: A4
- Left margin: `56.69291`
- Right margin: `56.69291`
- Top content start: `PAGE_HEIGHT - 70`
- Bottom guard area: `62`
- Body line height: `14`

## Typography
- Title font: `Helvetica-Bold`, size `24`
- Title color: primary orange (`#ED5500`)
- Subtitle font: `Helvetica-Bold`, size `14`
- Section heading font (`##`): `Helvetica-Bold`, size `13`
- Body font: `Helvetica`, size `10.5`
- Code font: `Courier`, size `8.2`
- Footer font: `Helvetica`, size `9`

## Colors
- Primary orange (from contract):
  - RGB float: `(0.929412, 0.333333, 0)`
  - Hex: `#ED5500`
- Body text color: black
- Code block background: white
- Code block border: primary orange

## Footer (Every Page)
- Left footer text: `Neurolabs - Confidential Partner Documentation`
- Right footer text: `Neurolabs SDK - Page N`
- Separator line:
  - Color: primary orange
  - Y position: `43.93701`
  - From `LEFT` to `PAGE_WIDTH - RIGHT`

## Cover Block
- Render at the top of page 1:
  - Product-specific title (e.g., `Neurolabs Android SDK Integration Guide`)
  - Subtitle: `Technical Integration Specification`
  - Metadata lines:
    - `Document ID: ...`
    - `Version: ...`
    - `Date: YYYY-MM-DD`
    - `Status: Partner integration reference`
    - `Owner: Neurolabs`

## Markdown Mapping
- `# ...`
  - Ignore inside body flow (cover already renders title)
- `## ...`
  - Render as section heading
- Regular lines
  - Render as wrapped body text
- Lines starting with `- `
  - Render as bullet (`• `) + text
- Triple backticks fenced blocks
  - Render as boxed code block (orange border)

## Pagination Rules (Required)
- Never place a section heading as the last row of a page.
- Before rendering a `##` heading, ensure there is room for:
  - heading height (`22`) + small gap + the next content block start.
- If the next content block cannot begin below the heading on the same page,
  move the heading to the next page.
- Code blocks must not be split mid-box. If full block does not fit, move it to the next page.

## Regeneration Checklist
- Footer text and orange separator appear on every page.
- Primary orange color matches contract (`#ED5500`).
- No orphan section titles at page bottoms.
- Code samples are boxed with orange border.
- Output path remains `Neurolabs-Android-Integration-Guide.pdf` in repo root.

## Suggested Implementation
- Use the in-repo deterministic generator:
  - `neurolabs-mobile-dist/scripts/generate_markdown_pdf.py`
- Keep generation deterministic:
  - fixed margins, sizes, and line heights
  - no random layout behavior
- Parse markdown line-by-line (no dependency on external converters required).
