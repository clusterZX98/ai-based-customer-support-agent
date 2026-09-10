import json
from pathlib import Path

ORDER_FILE = Path("data/orders.json")


def get_order(order_id: str) -> dict:
    try:
        data = json.loads(ORDER_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"Unable to load order database: {e}"}

    order = data.get(order_id)

    if not order:
        return {"error": f"Order {order_id} was not found."}

    return order 