# Property failures

## P1 `test_p1_slow_payment_gives_error_within_3s`: REGRESSION (failed twice)

First run: `AssertionError: answered in 18.60s
assert 18.59864241699688 <= 3.0`

Re-run: `AssertionError: answered in 20.01s
assert 20.00866425014101 <= 3.0`

Measured (first run):

```json
[
  {
    "call": "checkout",
    "result": {
      "status": 504,
      "elapsed_s": 18.599,
      "body": {
        "error": "payment_timeout",
        "order_id": "2d410d7cb5b44af79ffc0123b51654bf",
        "status": "FAILED"
      }
    }
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     127.0.0.1:35008 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35020 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:52184 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:52196 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:52208 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:52218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:52230 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     127.0.0.1:36046 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36060 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36062 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36076 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36090 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:32994 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33008 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33024 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33038 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33052 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35866 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:54472 - "POST /admin/reset HTTP/1.1" 200 OK
```

## P1 `test_p3_payment_down_gives_clean_503`: REGRESSION (failed twice)

First run: `AssertionError: answered in 18.80s
assert 18.796729875029996 <= 3.0`

Re-run: `AssertionError: answered in 18.74s
assert 18.739676791010424 <= 3.0`

Measured (first run):

```json
[
  {
    "call": "checkout",
    "result": {
      "status": 503,
      "elapsed_s": 18.797,
      "body": {
        "error": "payment_unavailable",
        "order_id": "9dfde818b16448399350d042a81ce624",
        "status": "FAILED"
      }
    }
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:52230 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     127.0.0.1:36046 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36060 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36062 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36076 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36090 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:32994 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33008 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33024 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33038 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33052 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35866 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:54472 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33708 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33708 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35870 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35884 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35896 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41552 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41564 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41578 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41588 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41598 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:37086 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33708 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:33708 - "POST /admin/reset HTTP/1.1" 200 OK
```

## P4 `test_p4_payment_503_burst_bounded_retries`: REGRESSION (failed twice)

First run: `AssertionError: Payment received 11 attempts (checkout returned 200)
assert 11 <= 3`

Re-run: `AssertionError: Payment received 11 attempts (checkout returned 200)
assert 11 <= 3`

Measured (first run):

```json
[
  {
    "call": "checkout",
    "result": {
      "status": 200,
      "elapsed_s": 12.877,
      "body": {
        "order_id": "de3ae251c60149f584e4f29d1e2748ac",
        "status": "CONFIRMED",
        "charge_id": 1
      }
    }
  },
  {
    "call": "attempts",
    "result": 11
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     127.0.0.1:36046 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34724 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36060 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36062 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36076 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36090 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:32994 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33008 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33024 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33038 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:33052 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35866 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:54472 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:54472 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33708 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33708 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35870 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35884 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35896 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41552 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41564 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41578 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41588 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:41598 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:37086 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33708 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:33708 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:36936 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:36936 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:37090 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:37106 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:37118 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:37120 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:54448 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:54456 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:54470 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:36936 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:36936 - "POST /admin/reset HTTP/1.1" 200 OK
```

