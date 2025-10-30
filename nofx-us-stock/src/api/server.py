from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn


def create_app(manager: Any | None) -> FastAPI:
    app = FastAPI(title="NOFX US Stock API")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Legacy/basic routes
    @app.get("/traders")
    async def list_traders() -> list[dict[str, Any]]:
        cfg = getattr(manager, "config", None)
        return cfg.traders if cfg else []

    @app.get("/status/{trader_id}")
    async def get_status(trader_id: str) -> dict[str, Any]:
        return manager.status(trader_id)

    @app.get("/decisions/{trader_id}")
    async def get_decisions(trader_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return manager.recent_decisions(trader_id, limit=limit)

    class OrderRequest(BaseModel):
        symbol: str
        side: str
        quantity: int
        order_type: str = "market"

    @app.get("/account/{trader_id}")
    async def get_account(trader_id: str) -> dict[str, Any]:
        return await manager.get_account(trader_id)

    @app.get("/positions/{trader_id}")
    async def get_positions(trader_id: str) -> list[dict[str, Any]]:
        return await manager.get_positions(trader_id)

    @app.post("/orders/{trader_id}")
    async def place_order(trader_id: str, req: OrderRequest) -> dict[str, Any]:
        return await manager.place_order(trader_id, req.symbol, req.side, req.quantity, req.order_type)

    @app.post("/orders/{trader_id}/{order_id}/cancel")
    async def cancel_order(trader_id: str, order_id: str) -> dict[str, Any]:
        return await manager.cancel_order(trader_id, order_id)

    # ===== Frontend expected API (prefixed with /api and query params) =====
    @app.get("/api/competition")
    async def api_competition() -> dict[str, Any]:
        cfg = getattr(manager, "config", None)
        traders_cfg = cfg.traders if cfg else []
        out: list[dict[str, Any]] = []
        for t in traders_cfg:
            trader_id = t.get("id", "default")
            status = manager.status(trader_id)
            try:
                acct = await manager.get_account(trader_id)
            except Exception:
                acct = {"balance": 0.0}
            out.append({
                "trader_id": trader_id,
                "trader_name": t.get("name", trader_id),
                "ai_model": t.get("ai_model", "unknown"),
                "total_equity": float(acct.get("balance", 0.0)),
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "position_count": 0,
                "margin_used_pct": 0.0,
                "call_count": status.get("call_count", 0),
                "is_running": status.get("is_running", False),
            })
        return {"traders": out, "count": len(out)}

    @app.get("/api/traders")
    async def api_traders() -> list[dict[str, Any]]:
        cfg = getattr(manager, "config", None)
        traders_cfg = cfg.traders if cfg else []
        return [
            {
                "trader_id": t.get("id", "default"),
                "trader_name": t.get("name", t.get("id", "default")),
                "ai_model": t.get("ai_model", "unknown"),
            }
            for t in traders_cfg
        ]

    @app.get("/api/status")
    async def api_status(trader_id: str | None = None) -> dict[str, Any]:
        return manager.status(trader_id)

    @app.get("/api/account")
    async def api_account(trader_id: str | None = None) -> dict[str, Any]:
        if not trader_id:
            # fallback: 取第一个trader
            cfg = getattr(manager, "config", None)
            trader_id = cfg.traders[0]["id"] if cfg and cfg.traders else "default"
        return await manager.get_account(trader_id)

    @app.get("/api/positions")
    async def api_positions(trader_id: str | None = None) -> list[dict[str, Any]]:
        if not trader_id:
            cfg = getattr(manager, "config", None)
            trader_id = cfg.traders[0]["id"] if cfg and cfg.traders else "default"
        return await manager.get_positions(trader_id)

    @app.get("/api/decisions")
    async def api_decisions(trader_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if not trader_id:
            cfg = getattr(manager, "config", None)
            trader_id = cfg.traders[0]["id"] if cfg and cfg.traders else "default"
        return manager.recent_decisions(trader_id, limit=limit)

    @app.get("/api/decisions/latest")
    async def api_latest_decisions(trader_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return await api_decisions(trader_id, limit)

    @app.get("/api/statistics")
    async def api_statistics(trader_id: str | None = None) -> dict[str, Any]:
        if not trader_id:
            cfg = getattr(manager, "config", None)
            trader_id = cfg.traders[0]["id"] if cfg and cfg.traders else "default"
        # 使用logger汇总
        return getattr(manager, "_logger").summary(trader_id)

    @app.get("/api/equity-history")
    async def api_equity_history(trader_id: str | None = None) -> list[dict[str, Any]]:
        return []

    @app.get("/api/performance")
    async def api_performance(trader_id: str | None = None) -> dict[str, Any]:
        return {"win_rate": 0.0, "profit_factor": 0.0}

    return app


async def start_api_server(manager: Any | None, port: int = 8080) -> None:
    app = create_app(manager)
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


