from __future__ import annotations

from typing import Any


class DummyBrokerAPI:
    """与 market.dummy_data_api 中的 DummyBrokerAPI 等价的最小实现。"""

    def __init__(self) -> None:
        self._balance = 10000.0
        self._positions: dict[str, dict[str, Any]] = {}
        self._orders: dict[str, dict[str, Any]] = {}

    async def get_account(self) -> dict[str, Any]:
        return {"balance": self._balance}

    async def get_positions(self) -> list[dict[str, Any]]:
        return list(self._positions.values())

    async def place_order(self, symbol: str, side: str, quantity: int, order_type: str) -> dict[str, Any]:
        order_id = f"ord_{len(self._orders) + 1}"
        self._orders[order_id] = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "status": "filled",
        }
        pos = self._positions.get(symbol, {"symbol": symbol, "quantity": 0, "side": side})
        pos["quantity"] += quantity
        self._positions[symbol] = pos
        return self._orders[order_id]

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        order = self._orders.get(order_id)
        if not order:
            return {"order_id": order_id, "status": "not_found"}
        order["status"] = "canceled"
        return order


