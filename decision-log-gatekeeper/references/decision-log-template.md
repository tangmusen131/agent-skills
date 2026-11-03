# Decision Log Template

Copy and fill. Delete unused rows. Keep Decision / Discussion / Open separated.

```markdown
# Decision Log

| Field | Value |
|-------|-------|
| Source | meeting notes / chat export / other |
| Meeting or thread date | YYYY-MM-DD or unspecified |
| Participants | comma-separated or unknown |
| Timezone for due dates | e.g. Asia/Shanghai (UTC+8) |
| Log generated at | YYYY-MM-DD HH:MM TZ |

## Decisions

| ID | Decision (one sentence) | Owner | Due date | Status | Evidence (quote or line ref) |
|----|-------------------------|-------|----------|--------|------------------------------|
| D-001 | | Name or TBD | YYYY-MM-DD or TBD | proposed / accepted / done | |
| D-002 | | | | | |

Rules:
- Owner and Due date must come from the source text or stay `TBD`.
- Status defaults to `accepted` only when the source shows agreement; otherwise `proposed`.

## Discussion (explicitly not decided)

| ID | Topic | Viewpoints summarized | Why not a Decision |
|----|-------|-----------------------|--------------------|
| S-001 | | | no commitment language / parked / conflicted |

## Open items

| ID | Question or blocker | Suggested next ask | Related Decision IDs |
|----|---------------------|--------------------|----------------------|
| O-001 | | | |

## Follow-ups before publishing this log

- [ ] Resolve TBD owners
- [ ] Resolve TBD due dates (ask for calendar dates, not "soon")
- [ ] Confirm any ambiguous classifications with attendees

## Change record (optional)

| When | Who | What changed |
|------|-----|--------------|
| | | |
```
