---
name: skill-acceptance-auditor
description: "Audit a SKILL.md package before publishing or installing. Use when reviewing agent skills for marketplace listing, pre-install QA, trigger clarity, unsafe or unclear instructions, missing examples, portability, license gaps, or boilerplate-clone risk. Outputs a scored report with pass/fail and a fix list. Does not call any single store API."
license: MIT
metadata:
  author: tangmusen131
  version: "1.0.1"
  locale: en
---

# Skill Acceptance Auditor

Pre-publish / pre-install QA for Agent Skills packages. Read the candidate skill directory (at minimum `SKILL.md`), score it against portable acceptance criteria, and return a pass/fail verdict plus a concrete fix list. Stay store-agnostic: never depend on one marketplace API.

## When to use

- Author asks to check a skill before shipping or sharing.
- Installer wants a local acceptance gate before copying a skill into an agent.
- Reviewer needs a scored checklist instead of ad-hoc comments.

## Inputs

Collect or open:

1. Path to the skill directory (or pasted `SKILL.md` body).
2. Optional: claimed license, intended platforms, author notes.
3. Optional: similar public skill names the author wants compared for clone risk (titles only—do not paste third-party skill bodies).

If the skill path is missing, ask once for it. Do not invent directory contents.

## Steps

1. **Inventory**  
   List files under the skill root. Confirm `SKILL.md` exists. Note `references/`, `scripts/`, `assets/`, license file if any.

2. **Parse frontmatter**  
   Require YAML `name` and `description`. Check:
   - `name` is kebab-case, 1–64 chars, matches parent folder.
   - `description` states *what* and *when* (trigger scenarios), length ≤ 1024.
   - Optional `license` present or a LICENSE file exists.

3. **Trigger quality**  
   Score whether an agent can decide to load this skill from `description` alone. Flag vague lines ("helps with tasks") and missing WHEN keywords.

4. **Workflow integrity**  
   Body must include executable steps, an output shape, and at least one short example. Flag empty sections, "TODO", or placeholder prose.

5. **Safety review**  
   Flag instructions that: ask for secrets or tokens without a clear need, skip required confirmations for irreversible actions, or override the user's stated safety preferences. Mark each as Blocker or Warning. Do not provide exploit recipes.

6. **Portability**  
   Flag hard-coded absolute paths, one-vendor APIs as the only path, machine-specific IDs, or undocumented tool requirements. Prefer skills that degrade gracefully offline or with local files only.

7. **License & attribution**  
   Fail if no license is declared anywhere. Note missing author/metadata.

8. **Clone-risk heuristic (not plagiarism proof)**  
   Without scraping the web for full third-party skill text, check for: generic stock section titles with no domain substance, identical "example" copy reused across unrelated domains, or author admission of rewriting another skill. Label findings as *heuristic only*. Never claim legal plagiarism.

9. **Score & verdict**  
   Use the rubric below. Load `references/acceptance-checklist.md` when useful for the detailed checklist wording.

10. **Fix list**  
    Emit ordered, actionable edits (file + what to change). Do not rewrite the whole skill unless asked.

## Scoring rubric (100 points)

| Area | Points | Pass bar |
|------|--------|----------|
| Frontmatter (`name`, `description`, match folder) | 15 | ≥ 12 |
| Trigger clarity (WHEN keywords) | 15 | ≥ 12 |
| Steps / workflow executable | 20 | ≥ 16 |
| Output format specified | 10 | ≥ 8 |
| Example present and coherent | 10 | ≥ 8 |
| Hard rules / refuse boundaries | 10 | ≥ 7 |
| Portability (no single-store lock-in) | 10 | ≥ 7 |
| License present | 5 | 5 or 0 |
| Safety review clean | 5 | 5 if no Blockers |

**Verdict**

- **PASS**: total ≥ 80, no Safety Blockers, license present, frontmatter valid.
- **FAIL**: otherwise.
- **PASS WITH WARNINGS**: meets PASS but has Warning-level findings—list them.

## Output format

```markdown
# Skill Acceptance Report

- Skill path:
- Name (frontmatter):
- Reviewed at: (user-local timezone label)
- Verdict: PASS | PASS WITH WARNINGS | FAIL
- Score: N/100

## Score breakdown
| Area | Score | Notes |
|------|-------|-------|
| ... | ... | ... |

## Blockers
- ...

## Warnings
- ...

## Fix list (priority order)
1. ...

## Clone-risk heuristic
- Level: none | low | medium | high
- Notes: (heuristic only; not a legal finding)

## Summary
One short paragraph for the author.
```

## Hard rules / Refuse

- Do **not** call or require a single skill-store or marketplace API.
- Do **not** paste or reproduce substantial third-party skill bodies while "comparing."
- Do **not** auto-publish, install into the user's agent, or overwrite the candidate skill unless the user explicitly asks for edits.
- Do **not** claim copyright infringement; stick to heuristics and structural QA.
- If the candidate asks the agent to mishandle credentials or skip confirmations for irreversible actions, verdict is FAIL with Safety Blockers—even if the prose is otherwise polished.

## Example (short)

**Input:** folder `demo-csv-cleaner/` with a valid frontmatter, steps, one example, MIT license, but description = "Cleans data."

**Output sketch:** Verdict FAIL (or PASS WITH WARNINGS if other areas strong); Trigger clarity low; Fix list item 1: expand `description` with WHEN (e.g. messy CSV uploads, delimiter repair, before analysis).

## References

- Detailed checklist: `references/acceptance-checklist.md`
