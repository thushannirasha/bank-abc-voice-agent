from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from langsmith import traceable

_FAKE_CUSTOMERS = {
    "cust_1001": {
        "pin": "1234",
        "name": "Ava Patel",
        "balance": 2534.75,
        "currency": "LKR",
        "card_id": "card_4321",
        "address": "12 Market St, Springfield",
    },
    "cust_2002": {
        "pin": "4321",
        "name": "Noah Kim",
        "balance": 998.12,
        "currency": "LKR",
        "card_id": "card_9876",
        "address": "89 River Rd, Lakeside",
    },
}


@traceable(name="verify_identity")
def verify_identity(customer_id: str, pin: str) -> bool:
    customer = _FAKE_CUSTOMERS.get(customer_id)
    return bool(customer and customer["pin"] == pin)


@traceable(name="get_recent_transactions")
def get_recent_transactions(customer_id: str, count: int) -> List[Dict]:
    now = datetime.utcnow()
    transactions = []
    for i in range(count):
        transactions.append(
            {
                "id": f"txn_{customer_id[-4:]}_{i}",
                "date": (now - timedelta(days=i)).strftime("%Y-%m-%d"),
                "merchant": ["Grocery Hub", "Metro Transit", "Coffee Spot"][i % 3],
                "amount": round(12.5 + (i * 3.2), 2),
                "currency": "LKR",
                "status": "posted",
            }
        )
    return transactions


@traceable(name="block_card")
def block_card(card_id: str, reason: str) -> str:
    return f"Card {card_id} has been blocked. Reason: {reason}"


@traceable(name="get_account_balance")
def get_account_balance(customer_id: str) -> Dict:
    customer = _FAKE_CUSTOMERS.get(customer_id)
    if not customer:
        return {"balance": 0.0, "currency": "LKR"}
    return {"balance": customer["balance"], "currency": customer["currency"]}
