---
name: company-summary
description: Generate a one-page company research report for interview prep. Use when the user asks to research a company, get a company overview, prepare for an interview, or understand a company's products, competitors, or market position.
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
---

# Company Summary Reporting

## Goal
Produce a structured, one-page Markdown report about a company that gives the user everything they need to walk into an interview informed: what the company does, how it makes money, who it competes with, how it's performing, and whether it's a smart career bet.

## Input
The user provides a **company name** (required). This may be:
- Passed directly as a skill argument: `/company-summary Acme Corp`
- Or stated conversationally: "research Stripe for me"

If no company name is provided, ask for it before proceeding.

## Research Process

Run the following web searches **in parallel** to gather broad, up-to-date information. Use the current year in queries to prioritize recent results.

### Search queries to run (all at once):
Substitute `{company}` with the actual company name and `{year}` with the current calendar year.

1. `"{company}" company overview mission products {year}`
2. `"{company}" business model revenue how they make money`
3. `"{company}" competitors market landscape alternatives`
4. `"{company}" funding valuation ARR growth {year}`
5. `"{company}" company culture employees Glassdoor leadership`
6. `"{company}" news announcements {year}`

After running searches, use `WebFetch` on 1–2 of the most authoritative result URLs (company homepage, Crunchbase, LinkedIn, reputable tech press) to deepen any sections that came back sparse.

## Report Template

Generate the report by filling in the template below. Replace every `[placeholder]` with synthesized, specific content from your research. Do not leave placeholders blank — if data is unavailable, write "Not publicly available" or your best inference labeled as such.

```markdown
# Company Summary: {Company Name}

*Report generated: {YYYY-MM-DD}*

---

## At a Glance

| Field | Detail |
|-------|--------|
| **Founded** | |
| **HQ** | |
| **Stage** | Public (NYSE/NASDAQ: TICKER) / Private (Series X) |
| **Employees** | |
| **Funding / Market Cap** | |
| **Website** | |

---

## Mission & Vision

> [Mission statement or tagline — quote directly if available]

[1–2 sentences on what problem they exist to solve and their long-term ambition.]

---

## Core Products & Services

### [Product / Service 1]
[What it does, who uses it, why it matters.]

### [Product / Service 2]
[Repeat as needed. Focus on the 2–4 most important offerings.]

---

## Business Model

[How do they make money? e.g., SaaS subscription, usage-based, marketplace take-rate, advertising, professional services, hardware + software, etc.]

**Key revenue drivers:**
- [Driver 1]
- [Driver 2]

---

## Target Market & Customers

- **Primary segment:** [e.g., mid-market B2B SaaS, enterprise healthcare, consumer]
- **Customer examples:** [Named logos or representative customer types]
- **Geography:** [US-only, global, primary markets]

---

## Competitive Differentiators

What makes them meaningfully different from alternatives:

1. [Differentiator 1 — be specific, not generic]
2. [Differentiator 2]
3. [Differentiator 3]

---

## Competitive Landscape

| Competitor | Positioning | Key Difference vs. {Company} |
|------------|-------------|-------------------------------|
| [Competitor 1] | [Their angle] | [How {Company} differs] |
| [Competitor 2] | [Their angle] | [How {Company} differs] |
| [Competitor 3] | [Their angle] | [How {Company} differs] |

---

## Recent News & Milestones *(Last 12 Months)*

- **[Month Year]:** [Event — product launch, funding round, acquisition, leadership change, partnership]
- **[Month Year]:** [Event]
- **[Month Year]:** [Event]

---

## Financial Health & Growth Signals

- **Revenue / ARR:** [Figure or "Not publicly available"]
- **Funding history:** [Total raised, last round, lead investors]
- **Growth trajectory:** [Growing / plateauing / contracting — with evidence]
- **Profitability:** [Profitable / pre-profitability / path to profitability noted]

---

## Company Culture & Team

- **CEO / Leadership:** [Name, background, tenure, notable traits]
- **Team size & growth:** [Headcount trend]
- **Culture signals:** [From Glassdoor, press, LinkedIn — be specific about what employees say]
- **Remote / hybrid / in-office:** [Policy]

---

## Strategic Risks & Challenges

1. [Risk 1 — e.g., heavy competition from well-funded incumbents]
2. [Risk 2 — e.g., dependence on a single platform/distribution channel]
3. [Risk 3 — e.g., regulatory exposure, macroeconomic sensitivity]

---

## Interview Prep Corner

### Smart questions to ask your interviewer:
1. [Question tied to a specific strategic moment or challenge identified above]
2. [Question about team/culture that shows you've done your homework]
3. [Question about the roadmap or where the company is headed]

### Talking points to weave into your answers:
- [Insight about their mission you can reference when asked "why us?"]
- [Specific product knowledge you can name-drop]
- [A recent development that shows you follow the space]

### Green / Yellow / Red flags:
- ✅ [A genuinely positive signal for career fit]
- ⚠️ [Something worth asking about or watching]
- 🔴 [A concern worth weighing before accepting an offer — only include if warranted]

---

*Sources: [List key URLs consulted]*
```

## Steps

### Step 1: Run research searches
Run all 6 search queries in parallel using `WebSearch`. Review results.

### Step 2: Deep-fetch key sources (optional but recommended)
If any section is thin after searches, use `WebFetch` on the company homepage or a Crunchbase/LinkedIn/press URL to fill gaps.

### Step 3: Generate the report
Fill in the template above with synthesized content. Be specific — avoid vague generalities like "they focus on innovation." Name real products, real competitors, real numbers.

### Step 4: Save the report
```bash
python3 ./scripts/save_report.py "COMPANY_NAME" <<'EOF'
REPORT_CONTENT
EOF
```
Replace `COMPANY_NAME` with the actual company name and `REPORT_CONTENT` with the full Markdown text of the report — do not pass the literal strings.

Returns JSON `{"file": "<abs_path>", "filename": "<name>"}`.

Confirm the output file path to the user and tell them the report is ready.

## Outputs
- A Markdown file saved to `./output/<company>_company_summary_<YYYY-MM-DD>.md`
- The report displayed inline in the conversation for immediate review

## Script Error Handling
If `save_report.py` exits non-zero or returns JSON with an `"error"` key:
1. Show the error to the user
2. Print the report content directly to the conversation as a fallback so the user still has it

## Edge Cases
- **Company not found / very obscure:** Note what's available and what couldn't be verified. Fill in what you can and flag gaps.
- **Conflicting data across sources:** Use the most recent, authoritative source and note the discrepancy.
- **Stealth / pre-launch company:** Focus on what's public (LinkedIn, founder backgrounds, investor list) and flag limited information clearly.
- **User wants a specific angle:** If the user says "focus on their AI strategy" or "I'm going for a sales role," weight the report accordingly.
