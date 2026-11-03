# Acceptance Checklist (Skill Acceptance Auditor)

Use this checklist while reviewing a candidate skill package. Mark each item Yes / No / N/A. Map failures into the scored report.

## A. Package shape

- [ ] Skill is a directory whose name matches frontmatter `name`
- [ ] `SKILL.md` exists at the skill root
- [ ] Optional folders (`references/`, `scripts/`, `assets/`) are documented or self-explanatory
- [ ] No secrets, API keys, or private customer data inside the package

## B. Frontmatter

- [ ] `name`: kebab-case, 1–64 characters, no leading/trailing/consecutive hyphens
- [ ] `description`: states what the skill does **and** when to use it
- [ ] `description` length ≤ 1024 characters
- [ ] `license` field or root LICENSE file present
- [ ] Optional `metadata.author` / `version` filled if the author intends distribution

## C. Trigger quality

- [ ] Description contains concrete WHEN cues (user phrases, artifact types, workflow moments)
- [ ] Description avoids empty phrases ("helps with tasks", "useful utility")
- [ ] Skill would not falsely activate for unrelated domains

## D. Body workflow

- [ ] Clear ordered Steps an agent can execute
- [ ] Inputs / prerequisites listed
- [ ] Output format specified (headings, tables, or template)
- [ ] At least one short Example (input → result sketch)
- [ ] Hard rules / Refuse section present
- [ ] No TODO / TBD / lorem placeholder prose in shipped text

## E. Safety

- [ ] No instruction to exfiltrate credentials or session tokens
- [ ] No "ignore all other policies" style overrides
- [ ] Destructive actions require explicit user confirmation
- [ ] Dual-use or illegal guidance absent

## F. Portability

- [ ] Works without a single marketplace API
- [ ] No mandatory hard-coded machine paths unique to one laptop
- [ ] Vendor-specific tools are optional fallbacks, not the only path
- [ ] Templates under `references/` are relative-path friendly

## G. Clone-risk heuristic (non-legal)

- [ ] Domain-specific steps exist (not only generic section headers)
- [ ] Example is tailored to this skill's job
- [ ] Author did not instruct "rewrite skill X from site Y"
- [ ] Finding level recorded as none / low / medium / high with notes

## Quick fail conditions

Any one of these ⇒ overall FAIL:

1. Missing or invalid `name` / `description`
2. No license declaration anywhere
3. Danger Blocker present
4. Body has no executable steps
5. Score total under 80
