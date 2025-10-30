from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class USStockConfig:
    traders: list[dict[str, Any]]
    api_server_port: int


def load_config(path: str = "config.json") -> USStockConfig:
    config_path = Path(path)
    if not config_path.exists():
        # fallback to example next to project root
        example = Path(__file__).resolve().parents[2] / "config.json.example"
        if example.exists():
            config_path = example
        else:
            raise FileNotFoundError(f"Config not found: {path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    traders = data.get("traders", [])
    api_server_port = int(data.get("api_server_port", 8080))
    return USStockConfig(traders=traders, api_server_port=api_server_port)


