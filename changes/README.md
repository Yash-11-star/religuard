# Change requests

The 8 change requests every agent receives, in this order. Each run starts from Version 0
(tag v0) and applies change 1..8 sequentially, each on top of that agent's previous version.

Rules for the study (keep runs comparable):
- Each agent receives preamble.txt followed by exactly one change_NN.txt, unedited.
- Same model version, same prompt text, no human edits to the code between changes.
- The agent's working copy must NOT contain properties/ (the harness removes it), so agents
  cannot see or run the reliability checks. tests/ stays, as a real team's repo would have it.
- Prompts are written like ordinary product tickets on purpose: they never mention reliability,
  faults, or the properties. Several are tempting on purpose (more retries, longer timeouts),
  because that is how real reliability regressions are introduced.

| # | Change | What it is likely to stress |
|---|--------|-----------------------------|
| 01 | Notification service after checkout | new dependency on the checkout path, latency budget |
| 02 | Retry payment more on transient failures | bounded retries, idempotency |
| 03 | Cache stock availability | consistency, stale reads |
| 04 | Rate limit checkout per customer | error handling, new state |
| 05 | Move notifications to a message queue | new infrastructure, failure isolation |
| 06 | Order status history table | DB writes in the checkout path, DB latency |
| 07 | Cancel order endpoint (refund + restock) | cross-service consistency, idempotency |
| 08 | Raise the payment timeout | deadlines, bounded latency |
