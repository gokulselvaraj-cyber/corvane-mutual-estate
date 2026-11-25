# quote-aggregator (planned)

**Status:** planned for 2027. **No code yet.** Proposed owner: team-distribution.

An adapter that will take quote requests from the CompareCover price-comparison feed, ask policy-admin for a price
(`POST /v1/quotes`) and send the result back in CompareCover's format. It is meant for Motor and Home first.

Open questions before any build:

- Whether quotes from the aggregator go through the same premium engine switch (`policy.premium-engine`) as the portal.
- How the aggregator's per-click fee is charged to the product lines.
- Whether broker commission applies to aggregator business (today's terms say no).

Nothing in this folder is deployed. There is no catalogue entry and no CODEOWNERS rule yet.
