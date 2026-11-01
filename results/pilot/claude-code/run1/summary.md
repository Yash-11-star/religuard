# Pilot: Claude Code (claude-sonnet-5-5, CLI 2.1.309), run 1

How it was run: `harness/pilot.md`. Raw files per change: `change_NN/`.

## Agent runs

| Change | Agent time | Turns | Cost (USD) | Files changed | Lines | Agent's own tests |
|---|---|---|---|---|---|---|
| baseline v0 | | | | | | 30/30 |
| 01 Notification service | 84.4 s | 9 | 0.286 | 11 | +311 / −22 | 43/43 |
| 02 Retry payment more | 104.0 s | 7 | 0.209 | 3 | +91 / −22 | 47/47 |

## Property checks

`pass` = passed first time; `FAIL` = failed on the run and on the single re-run.

The v0 and change 02 columns are from the re-measurement with the fixed checks
(`6-property-checks` @ `9c65d44`, raw files in `remeasure_9c65d44/`). Change 01 is from the
original pilot run (`7061ad2`) and was not re-measured: its P4 already recorded 3 attempts, and
its P8 second case ran as 503 × 10, not Payment down.

| Property | v0 | change 01 | change 02 |
|---|---|---|---|
| P1 Payment +5 s latency → error ≤ 3 s | pass | pass | **FAIL**: 504 after 18.60 s (re-run 20.01 s) |
| P2 Inventory +5 s latency → error ≤ 3 s | pass | pass | pass |
| P3 Payment down → clean 503 ≤ 3 s | pass | pass | **FAIL**: 503 `payment_unavailable` after 18.80 s (re-run 18.74 s) |
| P4 Payment 503 × 10 → ≤ 3 attempts | pass | pass (3 attempts) | **FAIL**: **11 attempts**; checkout returned 200 CONFIRMED after 12.88 s (re-run: 11 attempts, 13.38 s) |
| P5 Lost charge response → 1 charge | pass | pass | pass |
| P6 Duplicate delivery → 1 charge (sequential, concurrent) | pass | pass | pass |
| P7 Payment restored → success ≤ 10 s | pass | pass | pass |
| P8 Payment fails → stock released (decline) | pass | pass | pass: 402 in 0.006 s, stock 100/0 before and after |
| P8 Payment fails → stock released (Payment down) | pass | pass¹ | pass: 503 after 18.42 s, stock 100 available / 0 reserved before and after |
| P9 No PENDING after faults | pass | pass | pass |
| P10 order_db +1.5 s → graceful error ≤ 3 s | pass | pass | pass |

¹ Not run with Payment down: change 01 was measured with the old 503 × 10 case, which passed.

Change 01: no regressions. Change 02: three regressions (P1, P3, P4).

## Causes (change 02, `services/order/app.py` in the agent's commit `83a9f0e`)

- **P1, P3 (bounded latency):** `charge()` no longer receives the checkout deadline; it calls
  Payment with `Deadline(PAYMENT_RETRY_WINDOW)` (line 195) where `PAYMENT_RETRY_WINDOW = 20.0`
  (line 40). A slow or unreachable Payment is now retried for ~20 s before checkout answers, so the
  2.5 s whole-checkout deadline no longer bounds the response. The agent also replaced the existing
  test that asserted "answers within 3 s" with one asserting a 504 after the retry window.
- **P4 (bounded retries):** `max_attempts=PAYMENT_MAX_ATTEMPTS` (line 196) with
  `PAYMENT_MAX_ATTEMPTS = 30` (line 41) replaces the cap of 3. Payment received 11 attempts: ten
  forced 503s, then a success. This is exactly what the ticket asked for ("keep retrying"), which is
  why it is a reliability regression and not a functional bug: the agent's own tests pass.

## Check fixes after the pilot (`9c65d44`, PR #38, Refs #8)

The original pilot run (`7061ad2` checks, raw files in `change_02/`) showed two problems with the
checks themselves, both fixed and re-measured above:

- **P4** asserted "checkout failed" before reading the attempt count, so on change 02 it stopped
  at the status assert and the count was not recorded. It now reads `attempts()` first.
- **P8 [503]** assumed ten 503s make the payment fail. Under change 02 the payment eventually
  succeeded and stock was correctly committed, so the check failed although no reservation leaked.
  It is replaced by **P8 [payment_down]**: the Payment proxy is disabled for the whole checkout,
  which no retry policy can outlast. Change 02 passes it (stock released after the 18 s give-up).

## Caveats

- **Change 01's new notification path is not exercised by any property**: the checks never send
  `customer_email`, so faults on the new Notification dependency are untested.
