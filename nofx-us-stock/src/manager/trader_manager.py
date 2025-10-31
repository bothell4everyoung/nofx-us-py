from __future__ import annotations

from typing import Any
import asyncio
import logging

from trader.auto_trader import AutoTrader, AutoTraderConfig

logger = logging.getLogger(__name__)


class TraderManager:
    """Trader管理器（对应 Go 版本的 TraderManager）
    
    负责管理多个 AutoTrader 实例，提供统一的启动/停止/查询接口。
    """
    
    def __init__(self, config: Any) -> None:
        self.config = config
        self.traders: dict[str, AutoTrader] = {}  # key: trader ID
        self._tasks: dict[str, asyncio.Task] = {}
    
    def add_trader(self, trader_cfg: dict[str, Any]) -> None:
        """添加一个trader（对应 Go 版本的 AddTrader）"""
        trader_id = trader_cfg.get("id", "default")
        
        if trader_id in self.traders:
            raise ValueError(f"trader ID '{trader_id}' 已存在")
        
        # 构建AutoTraderConfig
        auto_config = AutoTraderConfig(
            id=trader_id,
            name=trader_cfg.get("name", trader_id),
            ai_model=trader_cfg.get("ai_model", "deepseek"),
            ai_api_key=trader_cfg.get("ai_api_key", ""),
            scan_interval_minutes=int(trader_cfg.get("scan_interval_minutes", 3)),
            initial_balance=float(trader_cfg.get("initial_balance", 10000.0)),
            btc_eth_leverage=int(trader_cfg.get("btc_eth_leverage", 10)),
            altcoin_leverage=int(trader_cfg.get("altcoin_leverage", 5)),
            stocks=trader_cfg.get("stocks", None),
        )
        
        # 创建trader实例
        try:
            trader = AutoTrader(auto_config)
            self.traders[trader_id] = trader
            logger.info(f"✓ Trader '{auto_config.name}' ({auto_config.ai_model}) 已添加")
        except Exception as e:
            raise ValueError(f"创建trader失败: {e}") from e
    
    def get_trader(self, trader_id: str) -> AutoTrader | None:
        """获取指定ID的trader（对应 Go 版本的 GetTrader）"""
        return self.traders.get(trader_id)
    
    def get_all_traders(self) -> dict[str, AutoTrader]:
        """获取所有trader（对应 Go 版本的 GetAllTraders）"""
        return self.traders.copy()
    
    def get_trader_ids(self) -> list[str]:
        """获取所有trader ID列表（对应 Go 版本的 GetTraderIDs）"""
        return list(self.traders.keys())
    
    async def start_all(self) -> None:
        """启动所有trader（对应 Go 版本的 StartAll）"""
        logger.info("🚀 启动所有Trader...")
        
        # 先添加所有trader（如果还未添加）
        for trader_cfg in self.config.traders:
            trader_id = trader_cfg.get("id", "default")
            if trader_id not in self.traders:
                self.add_trader(trader_cfg)
        
        # 启动所有trader
        for trader_id, trader in self.traders.items():
            logger.info(f"▶️  启动 {trader.get_name()}...")
            task = asyncio.create_task(trader.run())
            self._tasks[trader_id] = task
    
    async def stop_all(self) -> None:
        """停止所有trader（对应 Go 版本的 StopAll）"""
        logger.info("⏹  停止所有Trader...")
        for trader in self.traders.values():
            trader.stop()
        # 取消所有任务
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
    
    async def get_comparison_data(self) -> dict[str, Any]:
        """获取对比数据（对应 Go 版本的 GetComparisonData）"""
        traders_list = []
        
        for trader_id, trader in self.traders.items():
            try:
                account = await trader.get_account_info()
                status = trader.get_status()
                
                traders_list.append({
                    "trader_id": trader_id,
                    "trader_name": trader.get_name(),
                    "ai_model": trader.get_ai_model(),
                    "total_equity": account["total_equity"],
                    "total_pnl": account["total_pnl"],
                    "total_pnl_pct": account["total_pnl_pct"],
                    "position_count": account["position_count"],
                    "margin_used_pct": account["margin_used_pct"],
                    "call_count": status["call_count"],
                    "is_running": status["is_running"],
                })
            except Exception as e:
                logger.warning(f"获取trader {trader_id} 数据失败: {e}")
                continue
        
        return {
            "traders": traders_list,
            "count": len(traders_list),
        }
    
    # === 兼容旧API（供现有代码使用）===
    
    def status(self, trader_id: str | None = None) -> dict[str, Any]:
        """获取状态（兼容旧API）"""
        if trader_id:
            trader = self.get_trader(trader_id)
            if trader:
                return trader.get_status()
            return {"is_running": False, "start_time": 0, "runtime_minutes": 0, "call_count": 0}
        
        # 如果没有指定trader_id，返回第一个trader的状态
        if self.traders:
            first_trader = next(iter(self.traders.values()))
            return first_trader.get_status()
        
        return {"is_running": False, "start_time": 0, "runtime_minutes": 0, "call_count": 0}
    
    def recent_decisions(self, trader_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """获取最近决策（兼容旧API）"""
        trader = self.get_trader(trader_id)
        if not trader:
            return []
        return trader.decision_logger.read_recent(trader_id, limit=limit)
    
    async def get_account(self, trader_id: str) -> dict[str, Any]:
        """获取账户信息（兼容旧API）"""
        trader = self.get_trader(trader_id)
        if not trader:
            return {"error": "trader_not_found"}
        return await trader.get_account_info()
    
    async def get_positions(self, trader_id: str) -> list[dict[str, Any]]:
        """获取持仓（兼容旧API）"""
        trader = self.get_trader(trader_id)
        if not trader:
            return []
        return await trader.trader.get_positions()
    
    async def place_order(self, trader_id: str, symbol: str, side: str, quantity: int, order_type: str) -> dict[str, Any]:
        """下单（兼容旧API）"""
        trader = self.get_trader(trader_id)
        if not trader:
            return {"error": "trader_not_found"}
        return await trader.trader.place_order(symbol=symbol, side=side, quantity=quantity, order_type=order_type)
    
    async def cancel_order(self, trader_id: str, order_id: str) -> dict[str, Any]:
        """撤单（兼容旧API）"""
        trader = self.get_trader(trader_id)
        if not trader:
            return {"error": "trader_not_found"}
        return await trader.trader.cancel_order(order_id)
