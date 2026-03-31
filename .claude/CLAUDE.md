# Skills Repo — Workflow & Conventions

## Overview
This repo contains reusable skills across a range of domains (web dev, lead outreach, cover letter generation, inbox management, shopping, and more). Follow repo conventions and keep changes minimal.

## Skill Structure
Each skill lives at `.claude/skills/<skill-name>/` and must contain a `SKILL.md`. Optional supporting files:
- `template.md` — reusable templates
- `examples/` — sample inputs/outputs
- `scripts/` — executable scripts

## Token Discipline (Very Important)
When creating or modifying a skill:
- Do NOT read the full body of other skills by default.
- You MAY scan other skills' frontmatter (the `---` block) for orientation purposes only — checking what skills exist, avoiding name conflicts, or confirming what tools are declared. Do not use frontmatter from other skills to infer conventions; follow the Skill Contract in this file instead.
- Only read the full body of: the new/target skill folder, the template folder (if present), and any shared utils explicitly referenced by the template or skill.
- If you believe you need to read another skill's full body, list the exact files and ask first.

## Skill Types & Workflows

Before starting any work, identify which type applies — then follow that workflow only.

**Type A — Code/Script skills** (skills that write, run, or orchestrate code or API calls)
1. Implement the change.
2. Run `code-reviewer`. Fix any FAIL findings and re-run until PASS.
3. Run `qa` for behavior changes. Fix failures and re-run until green.
4. Ship (commit/push/PR as appropriate).
- Skip `code-reviewer` for typos/comments/config-only changes.
- Skip `qa` for docs/style-only changes.

**Type B — Content/Prompt skills** (skills that are primarily instructions, prompts, or templates with no scripts)
1. Implement the change.
2. Do a self-review: is the prompt clear, unambiguous, and free of conflicting instructions?
3. Ship.

**Type C — Reference/Knowledge skills** (conventions, style guides, domain patterns)
1. Implement the change.
2. Verify accuracy of the content itself.
3. Ship.

## Skill Contract
- Each skill must have a frontmatter block with at minimum `name` and `description`.
- Include `allowed-tools` when the skill invokes any tools; omit it for pure prompt/content skills.
- Each skill should have clear inputs/outputs and minimal side effects.
- Prefer JSON-serializable inputs/outputs unless the skill's purpose requires otherwise.
- Add a short example for non-trivial skills.

## Self-Annealing (Default Behavior)
When a skill runs and produces an error — wrong API endpoint, missing parameter, bad auth, incorrect model ID, flawed logic — automatically patch the `SKILL.md` (and/or supporting files/scripts) so the same failure cannot recur.

1. Fix the immediate problem so the current run succeeds.
2. Patch the skill file with the fix.
3. Resume the original task.

Patch wrong values, missing steps, flawed script logic, and incorrect assumptions. Do NOT patch one-off environmental issues (network timeouts, rate limits) or user input errors.

## Subagent Specs
- `.claude/agents/code-reviewer.md`
- `.claude/agents/qa.md`
- `.claude/agents/research.md`