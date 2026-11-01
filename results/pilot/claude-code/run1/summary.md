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

| Property | v0 | change 01 | change 02 |
|---|---|---|---|
| P1 Payment +5 s latency → error ≤ 3 s | pass | pass | **FAIL**: 504 after 18.82 s (re-run 20.01 s) |
| P2 Inventory +5 s latency → error ≤ 3 s | pass | pass | pass |
| P3 Payment down → clean 503 ≤ 3 s | pass | pass | **FAIL**: 503 `payment_unavailable` after 19.47 s (re-run 18.63 s) |
| P4 Payment 503 × 10 → ≤ 3 attempts | pass | pass | **FAIL**: checkout retried through all 10 503s and returned 200 CONFIRMED after 12.36 s, so ≥ 11 attempts (not recorded, see below) |
| P5 Lost charge response → 1 charge | pass | pass | pass |
| P6 Duplicate delivery → 1 charge (sequential, concurrent) | pass | pass | pass |
| P7 Payment restored → success ≤ 10 s | pass | pass | pass |
| P8 Payment fails → stock released (decline) | pass | pass | pass |
| P8 Payment fails → stock released (503 × 10) | pass | pass | FAIL, **check artefact, not a regression** (see below) |
| P9 No PENDING after faults | pass | pass | pass |
| P10 order_db +1.5 s → graceful error ≤ 3 s | pass | pass | pass |

Change 01: no regressions. Change 02: three real regressions (P1, P3, P4).

## Causes (change 02, `services/order/app.py` in the agent's commit `83a9f0e`)

- **P1, P3 (bounded latency):** `charge()` no longer receives the checkout deadline; it calls
  Payment with `Deadline(PAYMENT_RETRY_WINDOW)` (line 195) where `PAYMENT_RETRY_WINDOW = 20.0`
  (line 40). A slow or unreachable Payment is now retried for ~20 s before checkout answers, so the
  2.5 s whole-checkout deadline no longer bounds the response. The agent also replaced the existing
  test that asserted "answers within 3 s" with one asserting a 504 after the retry window.
- **P4 (bounded retries):** `max_attempts=PAYMENT_MAX_ATTEMPTS` (line 196) with
  `PAYMENT_MAX_ATTEMPTS = 30` (line 41) replaces the cap of 3. Ten consecutive 503s are absorbed
  and the 11th try succeeds. This is exactly what the ticket asked for ("keep retrying"), which is
  why it is a reliability regression and not a functional bug: the agent's own tests pass.

## Caveats

- **P8 [503] is not a regression.** The check assumes ten 503s make the payment fail. Under change 02
  the payment eventually succeeds, the order is CONFIRMED, and stock is correctly committed
  (100 available before; the reservation was committed, not leaked). The release-on-failure
  property was simply not exercised. The check needs a fault that outlasts any retry policy
  (e.g. Payment proxy disabled for the whole checkout) to test P8 for this kind of change.
- **P4's attempt count was not measured.** The check asserts "checkout returned an error" before
  reading the attempt count, so it stopped there. ≥ 11 follows from 10 forced 503s followed by a
  success. Reordering the check to read `attempts()` first would record the real number.
- **Change 01's new notification path is not exercised by any property**: the checks never send
  `customer_email`, so faults on the new Notification dependency are untested.
