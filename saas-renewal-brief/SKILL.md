---
name: saas-renewal-brief
description: "Build a SaaS renewal negotiation brief from user-supplied invoices, usage stats, and contract excerpts. Use when the user faces a renewal, wants leverage points, alternative cost ranges, must-have clauses, or a walk-away line. Always states this is not legal advice."
license: MIT
metadata:
  author: tangmusen131
  version: "1.0.0"
  locale: en
---

# SaaS Renewal Brief

Produce a practical renewal negotiation brief from materials the user provides (bills, usage exports, contract snippets, vendor emails). Focus on economics, leverage, must-have commercial terms, and a clear walk-away threshold. This is a **business briefing**, not legal counsel.

## When to use

- Renewal date is approaching and the user wants a one-pager for negotiation.
- User pasted invoice lines, seat/usage counts, or MSA/order-form excerpts.
- User asks for discount anchors, switching-cost estimates, or walk-away criteria.

## Inputs

Ask for whatever is missing among:

1. Vendor name and product tier.
2. Current annual (or monthly) spend and renewal quote if any.
3. Usage or seat metrics (active vs paid).
4. Contract excerpts: term, auto-renew, price uplift caps, termination, data export, SLA credits.
5. Known alternatives the user would actually consider.
6. Constraints: budget ceiling, mandatory integrations, compliance needs.

Do not scrape the vendor’s site for private account data. Public list prices may be cited with a date and source URL when the user wants market context.

## Steps

1. **Inventory facts**  
   Separate *stated in user materials* vs *assumed*. Label assumptions explicitly.

2. **Utilization & waste**  
   Compare paid capacity to observed usage. Quantify shelfware (unused seats, idle modules) in currency when numbers exist.

3. **Renewal math**  
   Show current run-rate, proposed renewal, % change, and multi-year implications if a longer term is on the table. If quote missing, mark “quote not provided.”

4. **Alternative cost (switching envelope)**  
   Build a rough envelope: substitute license + migration labor + risk buffer. Ranges are fine; inventing fake competitor quotes is not. If the user named no alternatives, list research questions instead of fake prices.

5. **Bargaining anchors**  
   Propose 2–3 discount or concession anchors grounded in waste, multi-year commit, competitive pressure, or removed modules—not arbitrary “ask 50% off.”

6. **Must-have commercial clauses**  
   From the user’s excerpts and goals, list clauses to request or preserve (uplift cap, termination for convenience, data export window, SLA credits, price hold on expansion). Flag anything that needs a lawyer for jurisdiction-specific enforceability.

7. **Walk-away**  
   Define a walk-away line: max acceptable total cost, minimum non-price terms, and the trigger to run the alternative path.

8. **Brief emission**  
   Use `references/renewal-brief-template.md`. Put the non-legal-advice disclaimer at the top of every brief.

## Output format

```markdown
# SaaS Renewal Brief — {vendor} / {product}

> **Not legal advice.** This brief is a business negotiation aid based on materials you provided.
> It is not a legal opinion, does not create an attorney-client relationship, and does not replace
> review by a qualified lawyer for your jurisdiction and contract.

## Snapshot
- Renewal date / notice window:
- Current spend vs quoted renewal:
- Utilization highlights:

## Fact vs assumption
| Item | Type | Notes |
|------|------|-------|

## Economics
- Waste / shelfware:
- Renewal math:
- Alternative cost envelope:

## Negotiation anchors
1. ...
2. ...

## Must-have terms (commercial)
- ...

## Walk-away
- Max price / structure:
- Non-price red lines:
- Switch trigger:

## Open questions for vendor / counsel
- ...

## Sources used
- User invoices / exports / excerpts (describe)
- Any public pages cited (URL + access date)
```

## Hard rules / Refuse

- **Always** include the “Not legal advice” disclaimer in the brief.
- Do **not** draft fake statutes, fake case law, or “guaranteed enforceable” clause language.
- Do **not** invent competitor prices; use user-supplied figures or clearly marked public ranges with sources.
- Do **not** encourage breach of contract, theft of data, or unauthorized system access as a “migration tactic.”
- If materials are insufficient, produce a partial brief plus a missing-info checklist—do not pad with fiction.
- Refuse requests to generate forged invoices, fake usage reports, or deceptive procurement documents.

## Example (short)

**User provides:** $48k/yr CRM quote (was $40k); 200 paid seats, 130 weekly actives; order form shows 8% auto uplift; alternatives not priced yet.

**Brief sketch:** Disclaimer first. Snapshot shows +20% uplift. Waste ≈ 70 seats. Anchors: seat true-up to 140, multi-year with uplift cap ≤ 3%, remove unused add-on. Walk-away: above $44k without uplift cap and export clause. Open questions: competitor quotes, notice period date.

## References

- Template: `references/renewal-brief-template.md`
