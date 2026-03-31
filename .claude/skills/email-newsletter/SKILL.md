---
name: email-newsletter
description: Generate and send "The Sotto Voce" — a weekly curated email newsletter covering world news, finance, sports, and culture. Runs every Monday at 5AM ET via cron. Supports Claude Dispatch for on-demand sends and config changes.
allowed-tools: Bash, Read, Write, Edit, WebSearch, WebFetch, Glob, Grep
---

# The Sotto Voce — Weekly Newsletter Skill

## Goal
Research, compile, and email a punchy, satirical weekly newsletter that covers world news, personal finance, sports, and culture — designed to be read in under 5 minutes on mobile.

## Newsletter Sections

### 1. News ("What's Going On")
- Cover **major world news and key US updates** from the past week.
- **Nonpartisan tone** — model after centrist/independent sources (The Free Press, Reuters, AP, The Dispatch, Axios).
- For **nuanced or controversial topics**, present both left and right perspectives. Clearly label which angle is which (e.g., "From the left: ... / From the right: ...").
- Include difficult or upsetting stories **only when they are genuinely significant** (e.g., active conflicts, major policy shifts). Skip doom-scroll fodder.
- Each bullet gets a **footnote citation** with source name and URL, collected at the bottom of the section.
- Aim for **4–6 bullets** max.

### 2. Finance ("Money Moves")
- Start with a **1–2 sentence macro snapshot** (S&P 500, NASDAQ, BTC weekly change, any major index moves).
- Then **2–4 actionable insights** — things that could actually change behavior for a 28-year-old equity/ETF + crypto investor. Examples:
  - Notable IPOs or S-1 filings (e.g., Anthropic, Stripe)
  - New legislation affecting 401k/IRA/Roth limits or tax strategy
  - New fintech products worth knowing about (credit cards, apps, platforms)
  - Real estate market signals relevant to a first-time buyer (rates, inventory, programs)
- Prioritize **"so what does this mean for me?"** over raw data.
- Include source links inline or as footnotes.

### 3. Sports ("The Scoreboard")
Content depth is tiered by league, but **do not label tiers in the output** — just vary the depth naturally.

**Tier 1 — NFL, NBA** (most detail):
- Key game results and highlights from the week
- Standings snapshot or playoff picture
- Notable trades, injuries, signings
- Hyperlink 1–2 **can't-miss highlights** to YouTube or league sites (no social media links)

**Tier 2 — MLB, UFC, NCAAF, NCAAB** (bigger stories only):
- Major trades, awards, upsets, or upcoming marquee events
- Only include if something noteworthy actually happened

**Tier 3 — Other / International** (rare):
- Only include for truly major events (Olympics, World Cup, historic achievements)
- Skip entirely most weeks

### 4. Other ("What Else is Happening")
- **3–5 quick-hit bullets** of pop culture, movies, music, tech, social trends.
- Tone: **uplifting and positive only.** No negativity, no outrage bait.
- This is the palette cleanser — fun, light, maybe a recommendation or two.

## Tone & Style
- **Satirical and funny** where it fits — think Grok, Morning Brew, The Hustle. Non-PC humor is fine, but punch up not down.
- **Punchy and concise** — short sentences, no fluff. Every word earns its spot.
- Use section headers with personality (the parenthetical names above are the defaults).
- Total read time target: **under 5 minutes.**

## Email Design
- **Mobile-first HTML** — single column, max-width 600px.
- Clear **section dividers** with distinct header colors:
  - News: #1a1a2e (dark navy)
  - Finance: #16813d (green)
  - Sports: #c0392b (red)
  - Other: #8e44ad (purple)
- Bold key phrases within bullets for scannability.
- Footer with: edition number, date, unsubscribe placeholder, and "Curated by Claude" tagline.
- Use the HTML template at `scripts/email_template.html` as the base.

## Delivery Configuration
- **Recipient:** christian.sottosanti@gmail.com
- **Schedule:** Every Monday at 5:00 AM ET
- **Sender:** Configured via Resend API (see setup below)
- **Subject line format:** `The Sotto Voce — Vol. {N} | {witty_one_liner_about_the_week}`
  - The one-liner should be a funny/clever summary of the biggest story of the week.

## Claude Dispatch Integration
This skill is connected to Claude Dispatch (remote triggers) so the user can:
- **Adjust frequency** — switch between weekly (default) and monthly
- **Change send time** — update the cron schedule
- **Request a one-off newsletter** — generate and send immediately
- **Add email addresses** — expand the distribution list

Dispatch commands are handled via the trigger configuration in `.claude/triggers/`.

## Technical Implementation

### Prerequisites
1. **Resend API key** — stored in environment variable `RESEND_API_KEY`
   - Sign up at https://resend.com (free tier: 100 emails/month)
   - Verify sender domain or use onboarding@resend.dev for testing
2. **Python 3.9+** with `requests` package installed

### How It Works
1. Cron trigger fires → launches this skill via Claude Code
2. Skill uses `WebSearch` and `WebFetch` to research each section (current week's news)
3. Content is compiled into the HTML email template
4. `scripts/send_newsletter.py` sends the email via Resend API
5. Edition number is tracked in `scripts/edition_tracker.json`

### Running Manually
```bash
# Generate and send immediately
cd .claude/skills/email-newsletter
python scripts/send_newsletter.py

# Or invoke via Claude Code
# "Send me this week's Sotto Voce"
```

### Search Queries by Section
When researching content, use these as starting points:

**News:**
- `"top news this week {date_range}"`
- `"major US news {date_range}"`
- `"world news highlights {date_range}"`
- Cross-reference: Reuters, AP News, The Free Press, Axios

**Finance:**
- `"stock market weekly recap {date_range}"`
- `"bitcoin crypto weekly {date_range}"`
- `"personal finance news {date_range}"`
- `"new fintech apps 2026"`
- `"first time home buyer news {date_range}"`

**Sports:**
- `"NFL news this week"`, `"NBA scores highlights this week"`
- `"MLB trades news"`, `"UFC fight results"`
- `"college football news"`, `"college basketball news"`

**Other:**
- `"trending pop culture this week"`
- `"best new movies music {date_range}"`
- `"uplifting news this week"`

## Execution Flow (Step by Step)

When this skill is triggered (by cron or manually):

1. **Read** `scripts/edition_tracker.json` to get the current edition number.
2. **Research** — Run web searches for each section (parallelize where possible). Gather 15–20 raw items across all sections.
3. **Curate** — Trim to the best items per section. Apply the tone/style guidelines. Write the satirical commentary.
4. **Format** — Inject content into the HTML template. Generate the subject line.
5. **Send** — Execute `scripts/send_newsletter.py` with the rendered HTML and subject.
6. **Update** edition tracker (increment number, record send date).
7. **Self-anneal** — If any step fails (bad API key, search fails, etc.), fix the skill files and retry.

## Example Subject Lines
- `The Sotto Voce — Vol. 12 | Congress Discovers the Internet (Again)`
- `The Sotto Voce — Vol. 7 | Bitcoin Did a Thing and Everyone Has Opinions`
- `The Sotto Voce — Vol. 23 | The Fed Said Words and Markets Had Feelings`
