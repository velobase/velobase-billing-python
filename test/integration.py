"""
Integration test for velobase-billing Python SDK.

Prerequisites:
    1. API server running on localhost:3002
    2. A valid API key in the local database

Usage:
    python test/integration.py
    API_KEY=vb_live_xxx BASE_URL=http://localhost:3002 python test/integration.py

Environment variables:
    API_KEY   — Velobase API key (required, or uses default)
    BASE_URL  — API base URL (default: http://localhost:3002)
"""

from __future__ import annotations

import asyncio
import os
import time

from velobase_billing import (
    AsyncVelobase,
    Velobase,
    VelobaseError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
)

API_KEY = os.environ.get("API_KEY", "vb_live_test_4ce5dc88e54a146bb290ad2460e48d52")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:3002")

# ─── Test harness ────────────────────────────────────────────────

passed = 0
failed = 0
failures: list[str] = []


def ok(cond: bool, msg: str = "") -> None:
    global passed, failed
    if not cond:
        failed += 1
        failures.append(msg)
        print(f"      ❌ FAIL: {msg}")
    else:
        passed += 1


# Unique prefix per run to avoid collision
RUN = f"py_{int(time.time()):x}"


def main() -> None:
    # ===================== 1. AUTH =====================
    print("════════════════���═════════════════")
    print(" 1. AUTH TESTS")
    print("══════════════════════════════════")

    print("\n  1.1 Empty API key → ValueError")
    try:
        Velobase(api_key="")
        ok(False, "should have thrown")
    except ValueError as e:
        ok("api_key is required" in str(e), "correct message")
        print(f'      OK: ValueError "{e}"')

    print("  1.2 Invalid API key → 401")
    try:
        vb_bad = Velobase(api_key="vb_live_fake", base_url=BASE_URL)
        vb_bad.customers.get("anyone")
        ok(False, "should have thrown")
    except AuthenticationError as e:
        ok(e.status == 401, "status=401")
        ok(e.type == "auth_error", "type=auth_error")
        ok(isinstance(e, VelobaseError), "isinstance VelobaseError")
        print(f'      OK: AuthenticationError {e.status} "{e.message}"')

    print("  1.3 Random string → 401")
    try:
        Velobase(api_key="garbage", base_url=BASE_URL).billing.freeze(
            customer_id="x", amount=1, transaction_id="b"
        )
        ok(False, "should have thrown")
    except AuthenticationError as e:
        ok(e.status == 401, "status=401")
        print(f"      OK: AuthenticationError {e.status}")

    vb = Velobase(api_key=API_KEY, base_url=BASE_URL)
    CUSTOMER = f"{RUN}_user"

    # ===================== 2. CUSTOMERS =====================
    print("\n══════════════════════════════════")
    print(" 2. CUSTOMER TESTS")
    print("══════════════════════════════════")

    print("\n  2.1 Get non-existent customer → 404")
    try:
        vb.customers.get("nonexistent_ghost_user")
        ok(False, "should have thrown")
    except NotFoundError as e:
        ok(e.status == 404, "status=404")
        print(f'      OK: NotFoundError "{e.message}"')

    print("  2.2 Deposit 1000 (creates customer)")
    d1 = vb.customers.deposit(
        customer_id=CUSTOMER, amount=1000, description="Initial deposit"
    )
    ok(d1.customer_id == CUSTOMER, "customer_id matches")
    ok(d1.added_amount == 1000, "added_amount=1000")
    ok(d1.total_amount == 1000, "total_amount=1000")
    ok(d1.is_idempotent_replay is False, "not idempotent replay")
    ok(isinstance(d1.account_id, str) and len(d1.account_id) > 0, "has account_id")
    ok(isinstance(d1.record_id, str) and len(d1.record_id) > 0, "has record_id")
    print(f"      OK: added={d1.added_amount} total={d1.total_amount}")

    print("  2.3 Get customer → verify balance")
    c1 = vb.customers.get(CUSTOMER)
    ok(c1.id == CUSTOMER, "id matches")
    ok(c1.balance.total == 1000, "total=1000")
    ok(c1.balance.used == 0, "used=0")
    ok(c1.balance.frozen == 0, "frozen=0")
    ok(c1.balance.available == 1000, "available=1000")
    ok(len(c1.accounts) >= 1, "has accounts")
    ok(c1.accounts[0].account_type == "CREDIT", "account_type=CREDIT")
    ok(c1.accounts[0].credit_type == "default", "credit_type=default")
    ok(isinstance(c1.created_at, str), "has created_at")
    print(f"      OK: total={c1.balance.total} available={c1.balance.available}")

    print("  2.4 Idempotent deposit (same idempotency_key)")
    idem_key = f"{RUN}_idem"
    d2 = vb.customers.deposit(
        customer_id=CUSTOMER, amount=500, idempotency_key=idem_key
    )
    ok(d2.is_idempotent_replay is False, "first call: not replay")
    d3 = vb.customers.deposit(
        customer_id=CUSTOMER, amount=500, idempotency_key=idem_key
    )
    ok(d3.is_idempotent_replay is True, "second call: is replay")
    c1b = vb.customers.get(CUSTOMER)
    ok(c1b.balance.available == 1500, "available=1500 (not 2000)")
    print(f"      OK: replay={d3.is_idempotent_replay} balance={c1b.balance.available}")

    # ===================== 3. BILLING FLOW =====================
    print("\n══════════════════════════════════")
    print(" 3. BILLING FLOW")
    print("══════════════════════════════════")

    print("\n  3.1 Freeze 600")
    txn1 = f"{RUN}_txn1"
    f1 = vb.billing.freeze(
        customer_id=CUSTOMER,
        amount=600,
        transaction_id=txn1,
        description="Video generation job",
    )
    ok(f1.transaction_id == txn1, "transaction_id matches")
    ok(f1.frozen_amount == 600, "frozen_amount=600")
    ok(f1.is_idempotent_replay is False, "not replay")
    ok(isinstance(f1.freeze_details, list) and len(f1.freeze_details) > 0, "has freeze_details")
    print(f"      OK: frozen={f1.frozen_amount}")

    print("  3.2 Balance after freeze")
    c2 = vb.customers.get(CUSTOMER)
    ok(c2.balance.frozen == 600, "frozen=600")
    ok(c2.balance.available == 900, "available=900")
    print(f"      OK: frozen={c2.balance.frozen} available={c2.balance.available}")

    print("  3.3 Idempotent freeze (same transaction_id)")
    f1b = vb.billing.freeze(customer_id=CUSTOMER, amount=600, transaction_id=txn1)
    ok(f1b.is_idempotent_replay is True, "is replay")
    print(f"      OK: is_idempotent_replay={f1b.is_idempotent_replay}")

    print("  3.4 Partial consume: 400 of 600 frozen")
    co1 = vb.billing.consume(transaction_id=txn1, actual_amount=400)
    ok(co1.transaction_id == txn1, "transaction_id matches")
    ok(co1.consumed_amount == 400, "consumed_amount=400")
    ok(co1.returned_amount == 200, "returned_amount=200")
    ok(co1.is_idempotent_replay is False, "not replay")
    ok(isinstance(co1.consumed_at, str), "has consumed_at")
    ok(isinstance(co1.consume_details, list), "has consume_details")
    print(f"      OK: consumed={co1.consumed_amount} returned={co1.returned_amount}")

    print("  3.5 Balance after partial consume")
    c3 = vb.customers.get(CUSTOMER)
    ok(c3.balance.total == 1500, "total=1500")
    ok(c3.balance.used == 400, "used=400")
    ok(c3.balance.frozen == 0, "frozen=0")
    ok(c3.balance.available == 1100, "available=1100")
    print(
        f"      OK: total={c3.balance.total} used={c3.balance.used} "
        f"frozen={c3.balance.frozen} available={c3.balance.available}"
    )

    print("  3.6 Freeze 300 → Unfreeze (full return)")
    txn2 = f"{RUN}_txn2"
    vb.billing.freeze(customer_id=CUSTOMER, amount=300, transaction_id=txn2)
    c4 = vb.customers.get(CUSTOMER)
    ok(c4.balance.frozen == 300, "frozen=300 after freeze")
    ok(c4.balance.available == 800, "available=800 after freeze")
    uf1 = vb.billing.unfreeze(transaction_id=txn2)
    ok(uf1.transaction_id == txn2, "transaction_id matches")
    ok(uf1.unfrozen_amount == 300, "unfrozen_amount=300")
    ok(uf1.is_idempotent_replay is False, "not replay")
    ok(isinstance(uf1.unfrozen_at, str), "has unfrozen_at")
    ok(isinstance(uf1.unfreeze_details, list), "has unfreeze_details")
    c5 = vb.customers.get(CUSTOMER)
    ok(c5.balance.frozen == 0, "frozen=0 after unfreeze")
    ok(c5.balance.available == 1100, "available=1100 after unfreeze")
    print(
        f"      OK: unfrozen={uf1.unfrozen_amount} → "
        f"frozen={c5.balance.frozen} available={c5.balance.available}"
    )

    print("  3.7 Full consume (no actual_amount)")
    txn3 = f"{RUN}_txn3"
    vb.billing.freeze(customer_id=CUSTOMER, amount=200, transaction_id=txn3)
    co2 = vb.billing.consume(transaction_id=txn3)
    ok(co2.consumed_amount == 200, "consumed_amount=200")
    ok(co2.returned_amount is None or co2.returned_amount == 0, "returned=None|0")
    c6 = vb.customers.get(CUSTOMER)
    ok(c6.balance.used == 600, "used=600")
    ok(c6.balance.available == 900, "available=900")
    print(
        f"      OK: consumed={co2.consumed_amount} returned={co2.returned_amount} "
        f"→ available={c6.balance.available}"
    )

    # ===================== 3B. DEDUCT FLOW =====================
    print("\n══════════════════════════════════")
    print(" 3B. DEDUCT FLOW")
    print("══════════════════════════════════")

    print("\n  3B.1 Direct deduct 50")
    txn_d1 = f"{RUN}_deduct1"
    dd1 = vb.billing.deduct(
        customer_id=CUSTOMER,
        amount=50,
        transaction_id=txn_d1,
        business_type="TASK",
        description="API call charge",
    )
    ok(dd1.transaction_id == txn_d1, "transaction_id matches")
    ok(dd1.deducted_amount == 50, "deducted_amount=50")
    ok(dd1.is_idempotent_replay is False, "not replay")
    ok(isinstance(dd1.deducted_at, str), "has deducted_at")
    ok(isinstance(dd1.deduct_details, list) and len(dd1.deduct_details) > 0, "has deduct_details")
    print(f"      OK: deducted={dd1.deducted_amount}")

    print("  3B.2 Balance after deduct")
    c7 = vb.customers.get(CUSTOMER)
    ok(c7.balance.used == 650, "used=650")
    ok(c7.balance.available == 850, "available=850")
    print(f"      OK: used={c7.balance.used} available={c7.balance.available}")

    print("  3B.3 Idempotent deduct (same transaction_id)")
    dd1b = vb.billing.deduct(
        customer_id=CUSTOMER, amount=50, transaction_id=txn_d1
    )
    ok(dd1b.is_idempotent_replay is True, "is replay")
    c7b = vb.customers.get(CUSTOMER)
    ok(c7b.balance.available == 850, "available still 850")
    print(f"      OK: replay={dd1b.is_idempotent_replay} available={c7b.balance.available}")

    print("  3B.4 Deduct insufficient balance")
    try:
        vb.billing.deduct(
            customer_id=CUSTOMER, amount=999999, transaction_id=f"{RUN}_deduct_fail"
        )
        ok(False, "should throw")
    except ValidationError as e:
        ok(e.status == 400, "status=400")
        print(f'      OK: ValidationError "{e.message}"')

    # ===================== 4. ERROR HANDLING =====================
    print("\n══════════════════════════════════")
    print(" 4. ERROR HANDLING")
    print("══════════════════════════════════")

    print("\n  4.1 Insufficient balance")
    try:
        vb.billing.freeze(
            customer_id=CUSTOMER, amount=999999, transaction_id=f"{RUN}_fail1"
        )
        ok(False, "should throw")
    except ValidationError as e:
        ok(e.status == 400, "status=400")
        print(f'      OK: ValidationError "{e.message}"')

    print("  4.2 Consume non-existent transaction_id")
    try:
        vb.billing.consume(transaction_id="nonexistent_txn_id")
        ok(False, "should throw")
    except VelobaseError as e:
        ok(e.status >= 400, "status>=400")
        print(f'      OK: {type(e).__name__} {e.status} "{e.message}"')

    print("  4.3 Deposit amount=0")
    try:
        vb.customers.deposit(customer_id=CUSTOMER, amount=0)
        ok(False, "should throw")
    except ValidationError as e:
        ok(e.status == 400, "status=400")
        print(f'      OK: ValidationError "{e.message}"')

    print("  4.4 Deposit amount=-1")
    try:
        vb.customers.deposit(customer_id=CUSTOMER, amount=-1)
        ok(False, "should throw")
    except ValidationError as e:
        ok(e.status == 400, "status=400")
        print(f'      OK: ValidationError "{e.message}"')

    print("  4.5 Freeze with empty customer_id")
    try:
        vb.billing.freeze(customer_id="", amount=100, transaction_id="x")
        ok(False, "should throw")
    except ValidationError as e:
        ok(e.status == 400, "status=400")
        print(f'      OK: ValidationError "{e.message}"')

    print("  4.6 Unfreeze non-existent transaction_id")
    try:
        vb.billing.unfreeze(transaction_id="nonexistent_txn_id")
        ok(False, "should throw")
    except VelobaseError as e:
        ok(e.status >= 400, "status>=400")
        print(f'      OK: {type(e).__name__} {e.status} "{e.message}"')

    # ===================== 5. ASYNC CLIENT =====================
    print("\n══════════════════════════════════")
    print(" 5. ASYNC CLIENT")
    print("══════════════════════════════════")

    async def test_async() -> None:
        ASYNC_CUSTOMER = f"{RUN}_async"
        avb = AsyncVelobase(api_key=API_KEY, base_url=BASE_URL)

        print("\n  5.1 Async deposit")
        d = await avb.customers.deposit(customer_id=ASYNC_CUSTOMER, amount=100)
        ok(d.added_amount == 100, "added=100")
        print(f"      OK: added={d.added_amount}")

        print("  5.2 Async get")
        c = await avb.customers.get(ASYNC_CUSTOMER)
        ok(c.balance.available == 100, "available=100")
        print(f"      OK: available={c.balance.available}")

        print("  5.3 Async freeze → consume")
        txn = f"{RUN}_async_txn"
        await avb.billing.freeze(
            customer_id=ASYNC_CUSTOMER, amount=50, transaction_id=txn
        )
        co = await avb.billing.consume(transaction_id=txn, actual_amount=30)
        ok(co.consumed_amount == 30, "consumed=30")
        print(f"      OK: consumed={co.consumed_amount}")

        print("  5.4 Async context manager")
        async with AsyncVelobase(api_key=API_KEY, base_url=BASE_URL) as client:
            c2 = await client.customers.get(ASYNC_CUSTOMER)
            ok(c2.balance.available == 70, "available=70")
            print(f"      OK: available={c2.balance.available}")

        await avb.close()

    asyncio.run(test_async())

    # ===================== 6. SYNC CONTEXT MANAGER =====================
    print("\n══════════════════════════════════")
    print(" 6. SYNC CONTEXT MANAGER")
    print("══════════════════════════════════")

    print("\n  6.1 with Velobase(...) as client:")
    with Velobase(api_key=API_KEY, base_url=BASE_URL) as client:
        c = client.customers.get(CUSTOMER)
        ok(c.balance.available == 850, "available=850")
        print(f"      OK: available={c.balance.available}")

    # ===================== SUMMARY =====================
    print("\n══════════════════════════════════")
    print(" RESULTS")
    print("══════════════════════════════════")
    print(f" Passed: {passed}/{passed + failed}")
    print(f" Failed: {failed}")
    if failures:
        print(" Failures:")
        for f in failures:
            print(f"   - {f}")
    if failed == 0:
        print(" ✅ ALL TESTS PASSED")
    else:
        print(" ❌ SOME TESTS FAILED")
        exit(1)


if __name__ == "__main__":
    main()
