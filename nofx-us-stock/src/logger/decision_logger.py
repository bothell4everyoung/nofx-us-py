from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json


class DecisionLogger:
    def __init__(self, dir_path: str) -> None:
        self.dir = Path(dir_path)
        self.dir.mkdir(parents=True, exist_ok=True)

    def log(self, trader_id: str, decision: dict[str, Any]) -> None:
        file = self.dir / f"{trader_id}.log"
        with file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")

    def read_recent(self, trader_id: str, limit: int = 50) -> list[dict[str, Any]]:
        file = self.dir / f"{trader_id}.log"
        if not file.exists():
            return []
        lines = file.read_text(encoding="utf-8").splitlines()[-limit:]
        out: list[dict[str, Any]] = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out

    def summary(self, trader_id: str) -> dict[str, Any]:
        records = self.read_recent(trader_id, limit=1000)
        total = len(records)
        buys = sum(1 for r in records if r.get("action") == "buy")
        sells = sum(1 for r in records if r.get("action") == "sell")
        holds = total - buys - sells
        return {"total": total, "buy": buys, "sell": sells, "hold": holds}


