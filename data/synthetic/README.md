# Synthetic Longitudinal Customer Dataset

Purpose:
A controlled, longitudinal dataset for a sales/meeting-preparation agent using persistent memory such as Hindsight.

Design:
- 10 synthetic companies
- 10 synthetic contacts
- 40 meetings (4 per customer)
- 80 emails (8 per customer)
- 40 commitments
- 30 decisions
- 40 concerns
- 20 learned contact preferences
- 10 relationship snapshots
- 230+ chronological events in events.jsonl

Longitudinal pattern:
Each customer has repeated interactions over time. Earlier concerns and commitments are intentionally referenced again later so an agent can demonstrate:
1. Remembering prior discussions
2. Detecting unresolved commitments
3. Detecting recurring concerns
4. Recalling previous decisions
5. Learning contact preferences
6. Preparing a future meeting using historical context

Recommended Hindsight ingestion:
- Retain meetings, emails, decisions, concerns and commitments as separate memories or event documents.
- Include customer_id and contact_id as metadata.
- Preserve event_date so temporal retrieval can be tested.
- Use PostgreSQL for deterministic records and Hindsight for semantic/relationship memory.

Important:
All people, companies, email addresses and events in this dataset are fictional and created for testing. They are not real customer records.

Suggested demo query:
"Prepare me for my next meeting with Sarah Mitchell at NexaCloud. What have we discussed before, what did I promise, what concerns keep coming up, and what changed recently?"
