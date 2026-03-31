---
name: web-mockup
description: Generate a complete single-file HTML mockup for a company or product, served live on localhost. Use when the user asks to prototype, mock up, build, or generate a web page or landing page for a company, product, or idea.
allowed-tools: Bash, Read, Write, WebFetch
---

# Web App Mockup Generator

## Goal
Generate a polished, single-file HTML mockup for a company or product using Tailwind CSS via CDN. The page should feel like a real, modern SaaS or marketing site. Claude generates the HTML directly in-context — no external API calls, no build steps, no extra cost.

## Design Rules

- Use **Tailwind CSS via CDN** — no build step, all classes inline
- **Mirror the source site's color palette** — use `WebFetch` on the source URL to extract CSS color values, hex codes, or visual style cues. Apply those colors (backgrounds, accents, text, buttons) to the mockup. Only fall back to defaults if no source URL is provided or color extraction fails.
- **Use real, publicly available images** where they enhance the design — check the source site for accessible image URLs (Squarespace CDN, etc.) and supplement with Unsplash (`https://images.unsplash.com/photo-<ID>?w=1200&q=80&fit=crop`). Verify images return HTTP 200 before embedding. Fall back to `https://placehold.co/` only if no real images are found.
- **Mobile-first responsive design** — all layouts should work on small screens and scale up
- Generate a **single self-contained `.html` file** — all styles and layout inline
- Do not introduce new frameworks, build steps, or external dependencies
- Prefer simple, deterministic layouts over clever abstractions
- Use realistic placeholder copy — not "Lorem Ipsum"

## Inputs

Collect these from the user before generating. Only #1 is required — offer sensible defaults for everything else.

1. **Company / product name** (required) — used for headings, page title, and filename
2. **Source URL** (optional) — scrape for real content (tagline, features, pricing, etc.)
3. **Design inspiration URL** (optional) — e.g. a godly.website link; scrape for aesthetic cues (layout style, color tone, typography feel)
4. **Sections to include** (optional) — e.g. "Hero, Features, Pricing, FAQ, Contact". Default: Hero + Features + CTA Footer
5. **External link** (optional) — the company's real website URL for nav/hero CTA buttons
6. **Extra instructions** (optional) — tone, color palette preferences, anything else

If the user invokes the skill without providing inputs, ask for them conversationally before proceeding.

## Scripts
All scripts are in `./scripts/`:
- `install_deps.py` — One-time setup: installs `beautifulsoup4`
- `scrape_url.py` — Fetches and extracts readable text from any URL
- `save_mockup.py` — Saves generated HTML from stdin to `output/`
- `serve_mockup.py` — Starts a local HTTP server and opens the file in the browser

## Process

All `python3` commands must be run from the skill root directory (the folder containing `SKILL.md`).

### Step 1: Ensure Dependencies
```bash
python3 ./scripts/install_deps.py
```
No-op if already installed.

### Step 2: Scrape Source URL (if provided)

**2a — Extract text content:**
```bash
python3 ./scripts/scrape_url.py "<source_url>"
```
Returns JSON `{"url": ..., "title": ..., "text": ...}`. Use the extracted text to inform the page copy — real taglines, feature names, pricing tiers, etc.

**2b — Extract visual style with WebFetch:**
Use `WebFetch` on the same source URL with this prompt:
> "Extract the exact color palette used on this page: hex codes or RGB values for background colors, text colors, accent/highlight colors, and button colors. Also list any real photography image URLs (jpg/png/webp) embedded in the page. Describe the typography style (serif vs sans-serif, weight, size hierarchy) and overall layout density."

Use the color values and image URLs extracted here to directly inform the mockup. If the page uses CSS variables or a framework that hides raw values, describe what colors are *visually* dominant.

If either step fails, skip and proceed without that context.

### Step 3: Scrape Design Inspiration URL (if provided)
```bash
python3 ./scripts/scrape_url.py "<template_url>"
```
Use the extracted text to understand the design aesthetic — note any color references, layout descriptions, typography style, or spacing patterns mentioned. Apply the feel to the generated HTML.

If scraping fails, skip and use a clean modern default aesthetic.

### Step 4: Generate HTML

Generate a complete, self-contained HTML mockup following the design rules above. The HTML must:

- Start with `<!DOCTYPE html>` and include a `<title>` set to the company/product name
- Load Tailwind via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Include all requested sections (or sensible defaults: Hero, Features, CTA Footer)
- Use realistic copy — not Lorem Ipsum. Invent plausible taglines, feature names, and benefit statements informed by the scraped content
- **Apply the extracted color palette** from Step 2b directly — background, accent, text, and button colors should match the source site's visual identity. Define custom colors in `tailwind.config` if needed.
- **Use real images** from Step 2b where available (verify 200 OK first). Supplement with thematically appropriate Unsplash photos (`https://images.unsplash.com/photo-<ID>?w=1200&q=80&fit=crop`) verified with `curl -s -o /dev/null -w "%{http_code}"`. Fall back to `https://placehold.co/` only as a last resort.
- Link hero/nav CTA buttons to the external link if provided, otherwise use `href="#"`
- Be fully responsive — use Tailwind's `sm:`, `md:`, `lg:` prefixes for breakpoints
- Look and feel like a real, polished modern site — not a template or a demo

Output the complete HTML inline in the conversation so the user can review it, then proceed to save.

### Step 5: Save Mockup
```bash
python3 ./scripts/save_mockup.py "Company Name" <<'EOF'
PASTE_FULL_HTML_HERE
EOF
```
Returns JSON `{"file": "<abs_path>", "filename": "<name>"}`. Note the output path.

### Step 6: Serve Mockup
```bash
python3 ./scripts/serve_mockup.py "<output_path>"
```
This starts a local server at `http://localhost:8080/<filename>` and opens it in the browser automatically.

If port 8080 is in use, retry with port 8081:
```bash
python3 ./scripts/serve_mockup.py "<output_path>" 8081
```

Tell the user the URL and that they can press Ctrl+C to stop the server.

## Outputs
- A single HTML file saved to `./output/<company>_mockup_<YYYYMMDD_HHMMSS>.html` (created once; overwritten on subsequent saves for the same company)
- The HTML displayed inline in the conversation for review
- A local server URL (`http://localhost:8080/<filename>`) opened in the browser

## Script Error Handling
If any script returns JSON with an `"error"` key or exits non-zero:
1. Show the error to the user
2. Follow the relevant fallback below
3. Do not proceed to the next step until the error is resolved or bypassed

## Edge Cases
- **Source URL scrape fails:** Proceed without scraped content; invent plausible copy based on the company name and any instructions
- **Template URL scrape fails:** Proceed with a clean, modern default aesthetic (dark hero, light sections, indigo/blue accent palette)
- **Color extraction fails / CSS variables hide values:** Use `WebFetch` to visually describe dominant colors, then pick the closest Tailwind equivalents. Prefer fidelity to the brand's general tone (warm vs. cool, muted vs. vibrant) over a generic default.
- **Image URL inaccessible (non-200):** Skip that image and try an alternative; never embed a broken image URL
- **Port 8080 in use:** Retry `serve_mockup.py` with port 8081; if that also fails, ask the user for a preferred port and pass it as the second argument to `serve_mockup.py`
- **User wants revisions:** Apply changes to the HTML, re-save (overwrites the existing file), and re-serve
- **No inputs provided:** Ask for company name (required) and offer to accept a URL for content; proceed with defaults for everything else

## Screenshot Reference Mode
_Activated only when the user provides a reference image or template screenshot._

1. **Generate** a single `index.html` using Tailwind CDN with all content inline
2. **Capture screenshots** of the rendered page (use Puppeteer or equivalent; create a minimal Puppeteer script if no tooling exists)
3. **Compare** against the reference — focus on:
   - Spacing and padding
   - Typography (size, weight, line height)
   - Colors (hex values when applicable)
   - Alignment and positioning
   - Border radius, shadows, visual effects
   - Responsive behavior
4. **Fix** all meaningful mismatches
5. **Re-capture** and compare again; repeat until major visual mismatches are resolved or the user instructs otherwise

### Comparison Principles
- Aim for visual parity, not pixel-perfect precision
- Ignore imperceptible sub-pixel or rendering-engine variance
- Prioritize structural/layout issues over tiny visual deviations
- Do not "improve" the reference — match it as-is; do not add unrequested sections or features
- Perform multiple passes for layout-sensitive tasks
