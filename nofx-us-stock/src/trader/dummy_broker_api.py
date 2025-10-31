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
        # 返回所有持仓，并确保格式正确
        result = []
        for key, pos in self._positions.items():
            if pos.get("quantity", 0) > 0:
                pos_copy = pos.copy()
                pos_copy["side"] = pos_copy.get("side", "long")
                pos_copy["entry_price"] = pos_copy.get("entry_price", 100.0)
                pos_copy["mark_price"] = pos_copy.get("mark_price", 100.0)
                pos_copy["unrealized_pnl"] = 0.0
                pos_copy["leverage"] = 1
                pos_copy["liquidation_price"] = None
                result.append(pos_copy)
        return result

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
        
        # 处理不同方向的订单
        pos_key = f"{symbol}_{side}"
        if side in ("sell", "cover"):
            # 平仓操作：减少持仓
            existing_pos_key = f"{symbol}_long" if side == "sell" else f"{symbol}_short"
            if existing_pos_key in self._positions:
                pos = self._positions[existing_pos_key]
                pos["quantity"] = max(0, pos["quantity"] - quantity)
                if pos["quantity"] == 0:
                    del self._positions[existing_pos_key]
        else:
            # 开仓操作：增加持仓
            existing_pos_key = f"{symbol}_long" if side in ("buy", "long") else f"{symbol}_short"
            if existing_pos_key not in self._positions:
                self._positions[existing_pos_key] = {
                    "symbol": symbol,
                    "quantity": 0,
                    "side": "long" if side in ("buy", "long") else "short",
                    "entry_price": 100.0,  # 默认价格
                    "mark_price": 100.0,
                }
            pos = self._positions[existing_pos_key]
            pos["quantity"] += quantity
        
        return self._orders[order_id]

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        order = self._orders.get(order_id)
        if not order:
            return {"order_id": order_id, "status": "not_found"}
        order["status"] = "canceled"
        return order


