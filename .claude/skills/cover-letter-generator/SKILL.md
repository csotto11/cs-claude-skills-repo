---
name: cover-letter
description: Generate a tailored cover letter by combining the user's resume with a job description (pasted text or URL). Use when the user asks to write, create, draft, or generate a cover letter for a job application.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# Cover Letter Generator

## Goal
Produce a polished, tailored cover letter in Markdown format by analyzing the user's resume against a specific job description and company, then highlighting the most relevant experiences through the lens of what that company values.

## Inputs
The user provides **one** of the following:
1. **Pasted job description text** — inline in the conversation
2. **Job posting URL** — a link to scrape for details

Optional inputs:
- **Company name** (if not obvious from the job description)
- **Specific experiences or talking points** to emphasize
- **Tone preference** (formal, conversational, etc. — default: professional but personable)

## Scripts
All scripts are in `./scripts/`:
- `install_deps.py` — One-time setup: installs `pypdf` for PDF parsing
- `parse_resume.py` — Extracts text from the most recent resume PDF
- `scrape_job_posting.py` — Fetches and extracts readable text from a job posting URL
- `save_cover_letter.py` — Saves the final cover letter markdown to `output/`

## Process

### Step 1: Ensure Dependencies
```bash
python3 ./scripts/install_deps.py
```
Only needed on first run. If `pypdf` is already installed, this is a no-op.

### Step 2: Parse Resume
```bash
python3 ./scripts/parse_resume.py
```
Returns JSON with the resume text. This always pulls the **most recently modified** resume PDF from `~/Desktop/Resume and Transcript/`.

### Step 3: Get Job Description

**If the user pasted text:** Use it directly — skip to Step 4.

**If the user provided a URL:**
```bash
python3 ./scripts/scrape_job_posting.py "URL"
```
Returns JSON with the extracted job posting text. If scraping fails, fall back to `WebFetch` or ask the user to paste the description.

### Step 4: Review Reference Examples
Read `./examples/reference_letters.md` for structural and tonal guidance. Note the key patterns:
- Specific company hook in the opening
- Quantified achievements mapped to job requirements
- Company-specific fit articulation
- 250-400 words, 3-4 paragraphs

### Step 5: Analyze and Draft
With resume text and job description in context:
1. Identify the **top 3-5 most relevant** experiences/skills from the resume that match the job requirements
2. Research or note anything specific about the company (recent news, mission, products) to weave into the opening hook
3. Draft a cover letter that **complements the resume rather than repeating it**:

   **Voice & Framing:**
   - The cover letter should tell a *narrative* the resume cannot — connect the dots between experiences, explain *why* this role and company, and convey how you think
   - Use the resume as *context* for what you've done, but the letter should focus on *insight, perspective, and fit* — the "so what" behind the bullet points
   - Reference experiences by theme and takeaway, not by restating specific metrics verbatim (e.g., say "I've built the playbooks that turn AI pilots into repeatable delivery machines" rather than "I documented 25+ processes")
   - At most **1-2 specific data points** from the resume — only when they're genuinely striking and directly relevant. The rest should be synthesized into broader narratives
   - Write like a sharp, self-aware professional — not a resume parser. Show judgment, not just accomplishments

   **Structure:**
   - Opens with a compelling hook tied to the **specific** role and company — never generic
   - Body paragraphs frame relevant experience through the lens of *what the company needs*, not a chronological recap
   - Bridges personal perspective to the company's specific challenges and culture
   - Closes with a confident call to action
   - Stays within **300-400 words** (3-4 paragraphs)

4. Present the draft to the user and ask if they want any changes

### Step 6: Save Output
After the user approves (or immediately if they didn't request review):
```bash
python3 ./scripts/save_cover_letter.py "COMPANY_NAME" <<'EOF'
COVER_LETTER_CONTENT
EOF
```
Confirm the output file path to the user.

## Outputs
- A Markdown file saved to `./output/<company>_cover_letter_<YYYY-MM-DD>.md`
- The cover letter text displayed in the conversation for review

## Script Error Handling
If any script returns JSON with an `"error"` key or exits with a non-zero code:
1. Display the error message to the user
2. Follow the relevant fallback from the Edge Cases section below
3. Do not proceed to the next step until the error is resolved or bypassed

## Edge Cases
- **No resume found:** Alert the user that no PDF was found in `~/Desktop/Resume and Transcript/` and ask for an alternative path
- **URL scrape fails:** Ask the user to paste the job description text instead
- **pypdf not installed and install fails:** Ask the user to paste their resume content directly
- **Very long job description:** Summarize the key requirements before drafting
- **User wants revisions:** Iterate on the draft, then save the final version
