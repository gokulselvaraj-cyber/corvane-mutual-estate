# ADR-0008: LLM-assisted fraud triage

- **Status:** Accepted
- **Date:** 2023-10-09
- **Deciders:** Platform architecture board

## Decision

fraud-scoring may call the internal AI gateway to summarise a claim and suggest a fraud referral. Behind the flag `fraud.llm-triage.enabled`. **Only the incident description and loss facts are sent; injury notes and other health data are never sent to the model.**

## Consequences

Adjusters get a readable summary. The model never makes the final decision: rules and humans do.
