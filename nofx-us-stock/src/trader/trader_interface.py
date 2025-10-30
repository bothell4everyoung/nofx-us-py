from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class USStockTrader(ABC):
    @abstractmethod
    async def get_account(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def buy_stock(self, symbol: str, shares: int) -> Dict[str, Any]:
        raise NotImplementedError


