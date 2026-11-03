---
name: decision-log-gatekeeper
description: "Turn meeting notes or chat transcripts into a strict decision log. Use when the user pastes standup notes, meeting minutes, Slack/Discord threads, or asks to extract decisions. Forces Decision vs Discussion vs Open labels; never silently invents unstated decisions; every Decision needs an owner and due date (TBD + ask if unknown)."
license: MIT
metadata:
  author: tangmusen131
  version: "1.0.0"
  locale: en
---

# Decision Log Gatekeeper

Convert raw meeting or chat text into a structured decision log. The gatekeeper's job is integrity: separate what was **decided**, what was only **discussed**, and what remains **open**—without inventing choices nobody stated.

## When to use

- User pastes meeting notes, call summaries, or chat exports and asks for a decision log.
- Team wants owners and due dates attached to each real decision.
- Facilitator needs a clean artifact after a messy thread.

## Inputs

1. Source text (notes, transcript excerpt, or chat dump).
2. Optional: meeting date, participants, timezone for due dates.
3. Optional: prior decision-log IDs to continue numbering.

If source text is empty, ask for it. Do not fabricate a meeting.

## Steps

1. **Read only what is present**  
   Work exclusively from the provided text and explicit user clarifications. Do not import "usual company practice" as a decision.

2. **Segment claims**  
   Split the source into candidate items. For each item, classify:
   - **Decision** — explicit commitment language ("we will", "agreed", "approved", "decided", "ship on…") tied to a clear action or choice.
   - **Discussion** — opinions, options, brainstorming, debates without closure.
   - **Open** — questions, blockers, or items parked for later ("TBD", "need to check", "circle back").

3. **Anti-invention gate**  
   If commitment language is missing, the item is **not** a Decision. Ambiguous lines go to Discussion or Open with a one-line reason. Never "helpfully" promote a Discussion into a Decision.

4. **Enrich Decisions only**  
   For each Decision, require:
   - **Owner** — named person or role from the text; else `TBD` and add a follow-up question.
   - **Due date** — explicit date/time from the text; else `TBD` and ask. Do not invent dates from "soon" or "next week" unless the user defines the calendar meaning in this session.
   - **Context** — one short quote or paraphrase pointing at the source line.
   - **ID** — `D-001`, `D-002`, … (or continue from prior IDs).

5. **Capture Discussion & Open**  
   Keep Discussion items brief (topic + viewpoints). Keep Open items as questions with suggested next ask.

6. **Follow-up questions block**  
   List every `TBD` owner/due date and any classification doubt. Ask the user before rewriting TBDs into real values.

7. **Emit the log**  
   Prefer the shape in `references/decision-log-template.md`.

## Output format

```markdown
# Decision Log
- Source: (meeting / chat / notes)
- Date: (from source or "unspecified")
- Participants: (if known)
- Generated: (user-local timezone label)

## Decisions
| ID | Decision | Owner | Due | Evidence (short) |
|----|----------|-------|-----|------------------|
| D-001 | ... | ... | ... | ... |

## Discussion (not decided)
| ID | Topic | Notes |
|----|-------|-------|
| S-001 | ... | ... |

## Open
| ID | Question / blocker | Suggested next ask |
|----|--------------------|--------------------|
| O-001 | ... | ... |

## Follow-ups required
- [ ] Owner for D-00X?
- [ ] Due date for D-00X?
```

## Hard rules / Refuse

- **Never silently complete** a decision that was not stated. No "they clearly meant X."
- **Never assign** an owner or due date that does not appear in the source; use `TBD` and ask.
- Do not merge Discussion into Decisions to make the log "look decisive."
- Do not drop minority objections from Discussion if they were recorded—summarize fairly.
- If the source is encrypted, inaccessible, or empty after redaction, stop and say so.
- This skill produces a log artifact, not legal minutes or HR records.

## Example (short)

**Input excerpt:**  
"We talked about blue vs green for the landing button. Alice likes blue. Nobody picked. Bob said he will send the pricing sheet by Friday. We agreed to freeze the API path as /v2/orders."

**Result sketch:**

- **D-001** Freeze API path `/v2/orders` — Owner TBD (ask who owns API) — Due TBD — Evidence: "agreed to freeze…"
- **D-002** Bob sends pricing sheet — Owner Bob — Due Friday (ask which calendar date) — Evidence: "Bob said he will send…"
- **Discussion S-001** Button color blue vs green — no decision
- **Open O-001** Who owns the API freeze follow-through?

## References

- Template: `references/decision-log-template.md`
