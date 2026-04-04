# velobase-billing

Official Velobase Billing SDK for Python.

- Synchronous and asynchronous clients
- Type-safe with Pydantic v2 models and `py.typed` support
- Automatic retries with exponential backoff
- Python 3.9+

## Installation

```bash
pip install velobase-billing
```

## Quick Start

```python
import uuid
from velobase_billing import Velobase

vb = Velobase(api_key="vb_live_xxx")

# 1. Deposit credits to a customer (creates the customer if new)
deposit = vb.customers.deposit(customer_id="user_123", amount=1000)

# 2. Check balance
customer = vb.customers.get("user_123")
print(customer.balance.available)  # 1000.0

# 3. Generate business_id once and persist before freezing
business_id = f"user_123_{uuid.uuid4().hex}"

# 4. Freeze credits before doing work
freeze = vb.billing.freeze(
    customer_id="user_123",
    amount=50,
    business_id=business_id,
)

# 5a. Job succeeded — consume (supports partial)
consume = vb.billing.consume(
    business_id=business_id,
    actual_amount=32,  # only charge 32, return 18
)

# 5b. Or if the job failed — unfreeze to return all
unfreeze = vb.billing.unfreeze(business_id=business_id)
```

## How It Works

Velobase Billing uses a **freeze-then-consume** pattern to safely manage credits:

```
deposit -> freeze -> consume   (normal flow)
                  -> unfreeze  (failure/cancellation)
```

1. **Deposit** — Add credits to a customer's account. Creates the customer automatically on first deposit.
2. **Freeze** — Pre-authorize an amount before performing work. The frozen credits are deducted from `available` but not yet `used`. Each freeze is identified by a unique `business_id` you provide.
3. **Consume** — After the work is done, settle the frozen amount. You can pass `actual_amount` to charge less than what was frozen; the difference is automatically returned.
4. **Unfreeze** — If the work fails or is cancelled, release the full frozen amount back to the customer.

All write operations are **idempotent** — repeating the same `business_id` (freeze/consume/unfreeze) or `idempotency_key` (deposit) returns the original result without double-charging.

## Async Usage

Every method is available in an async version via `AsyncVelobase`:

```python
from velobase_billing import AsyncVelobase

async def main():
    vb = AsyncVelobase(api_key="vb_live_xxx")

    deposit = await vb.customers.deposit(customer_id="user_123", amount=1000)
    customer = await vb.customers.get("user_123")
    print(customer.balance.available)

    await vb.close()
```

## Context Manager

Both clients support context managers to ensure the underlying HTTP connection is closed:

```python
# Sync
with Velobase(api_key="vb_live_xxx") as vb:
    customer = vb.customers.get("user_123")

# Async
async with AsyncVelobase(api_key="vb_live_xxx") as vb:
    customer = await vb.customers.get("user_123")
```

## Configuration

```python
vb = Velobase(
    api_key="vb_live_xxx",               # Required. Your Velobase API key.
    base_url="https://api.velobase.io",   # Optional. Override the API endpoint.
    timeout=30.0,                         # Optional. Request timeout in seconds (default: 30).
    max_retries=2,                        # Optional. Retry count on 5xx/network errors (default: 2).
)
```

## Usage Examples

### Deposit with idempotency

```python
# Safe to retry — the second call returns the same result without double-charging
result = vb.customers.deposit(
    customer_id="user_123",
    amount=500,
    idempotency_key="order_abc_payment",
    description="Purchase of 500 credits",
)

print(result.added_amount)         # 500.0
print(result.is_idempotent_replay) # False on first call, True on retries
```

### Deposit with customer metadata

```python
result = vb.customers.deposit(
    customer_id="user_123",
    amount=1000,
    name="Alice",
    email="alice@example.com",
    metadata={"plan": "pro", "source": "stripe"},
)
```

### Full billing flow

```python
CUSTOMER = "user_123"
JOB_ID = "video_gen_001"

# Check balance before starting
before = vb.customers.get(CUSTOMER)
print(f"Available: {before.balance.available}")

# Freeze the estimated cost
vb.billing.freeze(
    customer_id=CUSTOMER,
    amount=100,
    business_id=JOB_ID,
    business_type="TASK",
    description="1080p video, ~60s",
)

# ... do the work ...

# Settle with the actual cost (partial consumption)
result = vb.billing.consume(
    business_id=JOB_ID,
    actual_amount=73,
)
print(f"Charged: {result.consumed_amount}")   # 73.0
print(f"Returned: {result.returned_amount}")  # 27.0

# Verify final balance
after = vb.customers.get(CUSTOMER)
print(f"Available: {after.balance.available}")
```

### Customer balance structure

```python
customer = vb.customers.get("user_123")

# Aggregate balance across all accounts
customer.balance.total      # total deposited
customer.balance.used       # total consumed
customer.balance.frozen     # currently frozen (pending)
customer.balance.available  # total - used - frozen

# Individual accounts (e.g., different credit types/expiry)
for account in customer.accounts:
    print(account.account_type)      # "CREDIT"
    print(account.sub_account_type)  # "DEFAULT"
    print(account.available)
    print(account.expires_at)        # None or ISO date string
```

## API Reference

### `vb.customers.deposit(...) -> DepositResponse`

Deposit credits. Creates the customer if they don't exist.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `customer_id` | `str` | Yes | Your unique customer identifier |
| `amount` | `float` | Yes | Amount to deposit (must be > 0) |
| `idempotency_key` | `str` | No | Prevents duplicate deposits on retry |
| `name` | `str` | No | Customer display name |
| `email` | `str` | No | Customer email |
| `metadata` | `dict` | No | Arbitrary key-value metadata |
| `description` | `str` | No | Description for the deposit |

**Returns:** `DepositResponse` with fields `customer_id`, `account_id`, `total_amount`, `added_amount`, `record_id`, `is_idempotent_replay`

### `vb.customers.get(customer_id) -> CustomerResponse`

Retrieve a customer's balance and account details.

**Returns:** `CustomerResponse` with fields `id`, `name`, `email`, `metadata`, `balance`, `accounts`, `created_at`

### `vb.billing.freeze(...) -> FreezeResponse`

Freeze credits before performing work.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `customer_id` | `str` | Yes | Customer identifier |
| `amount` | `float` | Yes | Amount to freeze (must be > 0) |
| `business_id` | `str` | Yes | Your unique ID for this operation (idempotency key) |
| `business_type` | `BusinessType` | No | Business category. See [business_type](#business_type) for accepted values. |
| `description` | `str` | No | Human-readable description |

**Returns:** `FreezeResponse` with fields `business_id`, `frozen_amount`, `freeze_details`, `is_idempotent_replay`

### `vb.billing.consume(...) -> ConsumeResponse`

Settle a frozen amount. Supports partial consumption.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `business_id` | `str` | Yes | The `business_id` from the freeze |
| `actual_amount` | `float` | No | Actual amount to charge. Defaults to full frozen amount. |

**Returns:** `ConsumeResponse` with fields `business_id`, `consumed_amount`, `returned_amount`, `consume_details`, `consumed_at`, `is_idempotent_replay`

### `vb.billing.unfreeze(...) -> UnfreezeResponse`

Release a frozen amount back to the customer.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `business_id` | `str` | Yes | The `business_id` from the freeze |

**Returns:** `UnfreezeResponse` with fields `business_id`, `unfrozen_amount`, `unfreeze_details`, `unfrozen_at`, `is_idempotent_replay`

## `business_id`

`business_id` uniquely identifies one freeze → consume/unfreeze cycle and acts as its idempotency key. The server uses it to prevent double-charging on retries.

**Recommended format: `{customer_id}_{uuid}`**

```python
import uuid

# Generate once per billing operation, then persist it
business_id = f"{customer_id}_{uuid.uuid4().hex}"
# e.g. "user_123_a3f8c21d4e0b4a9f8c1d2e3f4a5b6c7d"
```

**Rules:**

- **Generate once and store** — create the UUID before calling `freeze()`, save it to your database, and reuse the same value on retries
- **Never regenerate at the call site** — calling `uuid.uuid4()` inside `freeze()` produces a different ID on every attempt, breaking idempotency
- **Unique within your project** — two different billing operations must not share the same `business_id`

```python
# Wrong — new UUID on every call, idempotency broken on retry
vb.billing.freeze(
    customer_id=customer_id,
    amount=50,
    business_id=f"{customer_id}_{uuid.uuid4().hex}",  # ❌ regenerated each time
)

# Correct — UUID generated once and persisted before calling freeze
business_id = db.get_or_create_business_id(operation_id, customer_id)
# e.g. db.get_or_create_business_id returns an existing ID or
#      stores f"{customer_id}_{uuid.uuid4().hex}" on first call

vb.billing.freeze(customer_id=customer_id, amount=50, business_id=business_id)
# Safe to retry — same business_id returns the original result
vb.billing.freeze(customer_id=customer_id, amount=50, business_id=business_id)
```

## business_type

`business_type` is an optional parameter on `freeze()` that categorises the billing operation for analytics and reconciliation. The SDK validates the value client-side and raises `ValueError` before sending any network request.

**Accepted values:**

| Value | Description |
|---|---|
| `"UNDEFINED"` | Default / unclassified (server default when omitted) |
| `"TASK"` | Async task execution (e.g. video generation, image processing) |
| `"ORDER"` | One-time purchase or order fulfilment |
| `"MEMBERSHIP"` | Membership plan credit grant |
| `"SUBSCRIPTION"` | Subscription renewal credit grant |
| `"FREE_TRIAL"` | Free-trial credit grant |
| `"ADMIN_GRANT"` | Manually granted credits by an admin |

```python
from velobase_billing import Velobase, BusinessType

vb = Velobase(api_key="vb_live_xxx")

vb.billing.freeze(
    customer_id="user_123",
    amount=50,
    business_id="job_abc",
    business_type="TASK",         # ✅ IDE autocomplete + client-side validation
)

vb.billing.freeze(
    customer_id="user_123",
    amount=50,
    business_id="job_abc",
    business_type="INVALID_VAL",  # ❌ raises ValueError before making a network call
)
```

## Error Handling

All API errors raise typed exceptions that inherit from `VelobaseError`:

```python
from velobase_billing import VelobaseError, ValidationError, AuthenticationError, NotFoundError

try:
    vb.billing.freeze(
        customer_id="user_123",
        amount=999999,
        business_id="job_xyz",
    )
except ValidationError as e:
    # 400 — bad request or insufficient balance
    print(e.message)  # "insufficient balance"
except AuthenticationError as e:
    # 401 — invalid or missing API key
    pass
except NotFoundError as e:
    # 404 — customer not found
    pass
except VelobaseError as e:
    # catch-all for other API errors
    print(e.status, e.type, e.message)
```

| Exception | HTTP Status | When |
|---|---|---|
| `AuthenticationError` | 401 | Invalid or missing API key |
| `ValidationError` | 400 | Bad params, insufficient balance |
| `NotFoundError` | 404 | Customer or resource not found |
| `ConflictError` | 409 | Conflicting operation |
| `InternalError` | 500 | Server-side error (auto-retried) |

## Retries

The SDK automatically retries on 5xx errors and network failures with exponential backoff (0.5s, 1s, 2s..., capped at 5s). Retries are safe because all Velobase write operations are idempotent.

4xx errors (validation, auth, not found) are never retried.

## License

MIT
