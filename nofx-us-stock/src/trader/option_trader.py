from __future__ import annotations

from typing import Any, Dict

from .dummy_broker_api import DummyBrokerAPI


class OptionTrader:
    def __init__(self, broker: DummyBrokerAPI | None = None) -> None:
        self.broker = broker or DummyBrokerAPI()

    async def buy_option(self, option_symbol: str, contracts: int) -> Dict[str, Any]:
        if contracts <= 0:
            return {"error": "invalid_contracts"}
        return await self.broker.place_order(symbol=option_symbol, side="buy", quantity=contracts, order_type="market")


