# Property failures

## P1 `test_p1_slow_payment_gives_error_within_3s`: REGRESSION (failed twice)

First run: `AssertionError: answered in 18.82s
assert 18.82286779116839 <= 3.0`

Re-run: `AssertionError: answered in 20.01s
assert 20.01336175017059 <= 3.0`

Measured (first run):

```json
[
  {
    "call": "checkout",
    "result": {
      "status": 504,
      "elapsed_s": 18.823,
      "body": {
        "error": "payment_timeout",
        "order_id": "8857549bd95a4ef0876c4c1cb2cc896d",
        "status": "FAILED"
      }
    }
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     127.0.0.1:54958 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:54964 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:54980 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35188 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35194 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35208 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     127.0.0.1:35210 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51198 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:42318 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51228 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51236 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51242 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35986 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35988 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35996 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36010 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36020 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59200 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
```

## P1 `test_p3_payment_down_gives_clean_503`: REGRESSION (failed twice)

First run: `AssertionError: answered in 19.47s
assert 19.473719832953066 <= 3.0`

Re-run: `AssertionError: answered in 18.63s
assert 18.6330236250069 <= 3.0`

Measured (first run):

```json
[
  {
    "call": "checkout",
    "result": {
      "status": 503,
      "elapsed_s": 19.474,
      "body": {
        "error": "payment_unavailable",
        "order_id": "e08b8e54dc4a45d989cf2f55eeba0378",
        "status": "FAILED"
      }
    }
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51198 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:42318 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51228 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51236 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51242 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35986 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35988 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35996 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36010 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36020 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59200 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59220 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59232 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59238 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59244 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43624 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43634 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43638 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43650 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43664 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:38152 - "POST /admin/reset HTTP/1.1" 200 OK
```

## P4 `test_p4_payment_503_burst_bounded_retries`: REGRESSION (failed twice)

First run: `AssertionError: expected an error, got 200: {"order_id":"befa80d6fc06417e92d2c1ec9b96d56d","status":"CONFIRMED","charge_id":1}
assert 200 >= 500
 +  where 200 = <Response [200 OK]>.status_code`

Re-run: `AssertionError: expected an error, got 200: {"order_id":"7dbc3382fad449ac8d3abfa459c3dd6c","status":"CONFIRMED","charge_id":1}
assert 200 >= 500
 +  where 200 = <Response [200 OK]>.status_code`

Measured (first run):

```json
[
  {
    "call": "checkout",
    "result": {
      "status": 200,
      "elapsed_s": 12.358,
      "body": {
        "order_id": "befa80d6fc06417e92d2c1ec9b96d56d",
        "status": "CONFIRMED",
        "charge_id": 1
      }
    }
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "GET /admin/orders?status=PENDING HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51198 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:42318 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51228 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51236 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51242 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35986 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35988 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35996 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36010 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36020 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59200 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59220 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59232 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59238 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59244 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43624 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43634 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43638 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43650 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43664 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:38152 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57316 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57346 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57362 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57374 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57386 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50616 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50632 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "POST /admin/reset HTTP/1.1" 200 OK
```

## P7 `test_p8_failed_payment_releases_reservation[503]`: REGRESSION (failed twice)

First run: `AssertionError: expected the checkout to fail, got 200: {"order_id":"f94ddced52d3409f89d7315e67993a6e","status":"CONFIRMED","charge_id":1}
assert 200 >= 400
 +  where 200 = <Response [200 OK]>.status_code`

Re-run: `AssertionError: expected the checkout to fail, got 200: {"order_id":"4c2f01f37ee245e3a29e6aa673e2dba9","status":"CONFIRMED","charge_id":1}
assert 200 >= 400
 +  where 200 = <Response [200 OK]>.status_code`

Measured (first run):

```json
[
  {
    "call": "stock",
    "result": {
      "sku": "SKU-1",
      "available": 100,
      "reserved": 0
    }
  },
  {
    "call": "checkout",
    "kwargs": {
      "qty": 3
    },
    "result": {
      "status": 200,
      "elapsed_s": 12.109,
      "body": {
        "order_id": "f94ddced52d3409f89d7315e67993a6e",
        "status": "CONFIRMED",
        "charge_id": 1
      }
    }
  }
]
```

Order service log, last 50 lines after the re-run:

```
order-1  | INFO:     172.18.0.1:42318 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51218 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51228 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51236 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:51242 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35986 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35988 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:35996 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36010 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:36020 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59200 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:34218 - "POST /checkout HTTP/1.1" 504 Gateway Timeout
order-1  | INFO:     172.18.0.1:34218 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59220 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59232 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59238 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:59244 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43624 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43634 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43638 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43650 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:43664 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:38152 - "POST /checkout HTTP/1.1" 503 Service Unavailable
order-1  | INFO:     172.18.0.1:38152 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57316 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57346 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57362 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57374 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:57386 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50616 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50632 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:33932 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:57030 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:57030 - "POST /admin/reset HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50646 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50660 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:50662 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:53406 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:53408 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:53420 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     127.0.0.1:53432 - "GET /health HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:57030 - "POST /checkout HTTP/1.1" 200 OK
order-1  | INFO:     172.18.0.1:57030 - "POST /admin/reset HTTP/1.1" 200 OK
```

