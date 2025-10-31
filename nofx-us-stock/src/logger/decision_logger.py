from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import math


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
    
    def get_latest_records(self, trader_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近的N条记录（对应 Go 版本的 GetLatestRecords）"""
        return self.read_recent(trader_id, limit=limit)

    def summary(self, trader_id: str) -> dict[str, Any]:
        records = self.read_recent(trader_id, limit=1000)
        total = len(records)
        buys = sum(1 for r in records if r.get("action") == "buy")
        sells = sum(1 for r in records if r.get("action") == "sell")
        holds = total - buys - sells
        return {"total": total, "buy": buys, "sell": sells, "hold": holds}
    
    def analyze_performance(self, trader_id: str, lookback_cycles: int = 20) -> dict[str, Any] | None:
        """分析最近N个周期的交易表现（对应 Go 版本的 AnalyzePerformance）
        
        包括：胜率、盈亏比、Sharpe Ratio 等指标
        """
        records = self.get_latest_records(trader_id, limit=lookback_cycles)
        
        if len(records) == 0:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "recent_trades": [],
                "symbol_stats": {},
                "best_symbol": "",
                "worst_symbol": "",
            }
        
        # 追踪持仓状态：symbol_side -> {side, openPrice, openTime, quantity, leverage}
        open_positions: dict[str, dict[str, Any]] = {}
        
        analysis = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "recent_trades": [],
            "symbol_stats": {},
        }
        
        # 遍历所有记录，追踪开仓和平仓
        for record in records:
            decisions = record.get("decisions", [])
            for action in decisions:
                symbol = action.get("symbol", "")
                action_type = action.get("action", "")
                
                if not symbol or not action_type:
                    continue
                
                pos_key = f"{symbol}_{action_type}"
                
                if action_type in ("open_long", "open_short"):
                    # 开仓：记录开仓信息
                    side = "long" if action_type == "open_long" else "short"
                    open_positions[f"{symbol}_{side}"] = {
                        "side": side,
                        "openPrice": action.get("price", 0.0),
                        "openTime": record.get("timestamp", ""),
                        "quantity": action.get("quantity", 0),
                        "leverage": action.get("leverage", 1),
                    }
                
                elif action_type in ("close_long", "close_short"):
                    # 平仓：计算盈亏
                    side = "long" if action_type == "close_long" else "short"
                    pos_key_close = f"{symbol}_{side}"
                    
                    if pos_key_close in open_positions:
                        open_pos = open_positions[pos_key_close]
                        open_price = float(open_pos["openPrice"])
                        close_price = float(action.get("price", 0.0))
                        quantity = float(open_pos["quantity"])
                        leverage = int(open_pos["leverage"])
                        
                        # 计算盈亏百分比
                        if side == "long":
                            pnl_pct = ((close_price - open_price) / open_price) * 100 if open_price > 0 else 0.0
                        else:
                            pnl_pct = ((open_price - close_price) / open_price) * 100 if open_price > 0 else 0.0
                        
                        # 计算实际盈亏（USD）
                        position_value = quantity * open_price
                        pnl = position_value * (pnl_pct / 100) * leverage
                        
                        # 记录交易结果
                        outcome = {
                            "symbol": symbol,
                            "side": side,
                            "open_price": open_price,
                            "close_price": close_price,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "open_time": open_pos["openTime"],
                            "close_time": record.get("timestamp", ""),
                        }
                        
                        analysis["recent_trades"].append(outcome)
                        analysis["total_trades"] += 1
                        
                        if pnl > 0:
                            analysis["winning_trades"] += 1
                            analysis["avg_win"] += pnl
                        else:
                            analysis["losing_trades"] += 1
                            analysis["avg_loss"] += pnl
                        
                        # 更新币种统计
                        if symbol not in analysis["symbol_stats"]:
                            analysis["symbol_stats"][symbol] = {
                                "symbol": symbol,
                                "total_trades": 0,
                                "winning_trades": 0,
                                "losing_trades": 0,
                                "total_pnl": 0.0,
                            }
                        
                        stats = analysis["symbol_stats"][symbol]
                        stats["total_trades"] += 1
                        stats["total_pnl"] += pnl
                        if pnl > 0:
                            stats["winning_trades"] += 1
                        else:
                            stats["losing_trades"] += 1
                        
                        # 移除已平仓记录
                        del open_positions[pos_key_close]
        
        # 计算统计指标
        if analysis["total_trades"] > 0:
            analysis["win_rate"] = (analysis["winning_trades"] / analysis["total_trades"]) * 100
            
            total_win_amount = analysis["avg_win"]
            total_loss_amount = analysis["avg_loss"]
            
            if analysis["winning_trades"] > 0:
                analysis["avg_win"] /= analysis["winning_trades"]
            if analysis["losing_trades"] > 0:
                analysis["avg_loss"] /= analysis["losing_trades"]
            
            # Profit Factor = 总盈利 / 总亏损（绝对值）
            if total_loss_amount != 0:
                analysis["profit_factor"] = total_win_amount / (-total_loss_amount)
            else:
                analysis["profit_factor"] = 0.0
        
        # 计算各币种胜率和平均盈亏
        best_pnl = -999999.0
        worst_pnl = 999999.0
        best_symbol = ""
        worst_symbol = ""
        
        for symbol, stats in analysis["symbol_stats"].items():
            if stats["total_trades"] > 0:
                stats["win_rate"] = (stats["winning_trades"] / stats["total_trades"]) * 100
                stats["avg_pnl"] = stats["total_pnl"] / stats["total_trades"]
                
                if stats["total_pnl"] > best_pnl:
                    best_pnl = stats["total_pnl"]
                    best_symbol = symbol
                if stats["total_pnl"] < worst_pnl:
                    worst_pnl = stats["total_pnl"]
                    worst_symbol = symbol
        
        analysis["best_symbol"] = best_symbol
        analysis["worst_symbol"] = worst_symbol
        
        # 只保留最近的交易（倒序：最新的在前）
        if len(analysis["recent_trades"]) > 10:
            analysis["recent_trades"] = analysis["recent_trades"][-10:]
        analysis["recent_trades"].reverse()
        
        # 计算夏普比率
        analysis["sharpe_ratio"] = self._calculate_sharpe_ratio(trader_id, records)
        
        return analysis
    
    def _calculate_sharpe_ratio(self, trader_id: str, records: list[dict[str, Any]]) -> float:
        """计算夏普比率（对应 Go 版本的 calculateSharpeRatio）
        
        基于账户净值的变化计算风险调整后收益
        """
        if len(records) < 2:
            return 0.0
        
        # 提取每个周期的账户净值
        equities: list[float] = []
        for record in records:
            account_state = record.get("account_state", {})
            equity = account_state.get("total_balance", 0.0)
            if equity > 0:
                equities.append(equity)
        
        if len(equities) < 2:
            return 0.0
        
        # 计算周期收益率（period returns）
        returns: list[float] = []
        for i in range(1, len(equities)):
            if equities[i - 1] > 0:
                period_return = (equities[i] - equities[i - 1]) / equities[i - 1]
                returns.append(period_return)
        
        if len(returns) == 0:
            return 0.0
        
        # 计算平均收益率
        mean_return = sum(returns) / len(returns)
        
        # 计算收益率标准差
        sum_squared_diff = sum((r - mean_return) ** 2 for r in returns)
        variance = sum_squared_diff / len(returns)
        std_dev = math.sqrt(variance)
        
        # 避免除以零
        if std_dev == 0:
            if mean_return > 0:
                return 999.0  # 无波动的正收益
            elif mean_return < 0:
                return -999.0  # 无波动的负收益
            return 0.0
        
        # 计算夏普比率（假设无风险利率为0）
        # 注：直接返回周期级别的夏普比率（非年化），正常范围 -2 到 +2
        sharpe_ratio = mean_return / std_dev
        return sharpe_ratio


