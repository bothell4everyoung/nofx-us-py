from __future__ import annotations

from typing import Any
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import time
import logging

from trader.stock_trader import StockTrader
from logger.decision_logger import DecisionLogger
from mcp.ai_client import AIClient
from decision.engine import (
    build_system_prompt,
    build_user_prompt,
    parse_full_decision_response,
    AccountInfo,
    PositionInfo,
    CandidateStock,
    Decision,
)
from market.stock_data import fetch_stock_with_indicators
# from pool.stock_pool import default_stock_universe  # 暂时注释，稍后实现

logger = logging.getLogger(__name__)


@dataclass
class AutoTraderConfig:
    """自动交易配置"""
    id: str
    name: str
    ai_model: str
    ai_api_key: str
    scan_interval_minutes: int = 3
    initial_balance: float = 10000.0
    btc_eth_leverage: int = 10
    altcoin_leverage: int = 5
    stocks: list[str] | None = None


class AutoTrader:
    """自动交易器（对应 Go 版本的 AutoTrader）"""
    
    def __init__(self, config: AutoTraderConfig) -> None:
        self.config = config
        self.id = config.id
        self.name = config.name
        self.ai_model = config.ai_model
        self.trader = StockTrader()
        self.ai_client = AIClient(model=config.ai_model, api_key=config.ai_api_key)
        self.decision_logger = DecisionLogger(
            str((__import__("pathlib").Path(__file__).resolve().parents[2] / "decision_logs" / config.id))
        )
        self.initial_balance = config.initial_balance
        self.daily_pnl = 0.0
        self.last_reset_time = datetime.now()
        self.stop_until: datetime | None = None
        self.is_running = False
        self.start_time = datetime.now()
        self.call_count = 0
        self.position_first_seen_time: dict[str, int] = {}
    
    async def run(self) -> None:
        """运行自动交易主循环（对应 Go 版本的 Run()）"""
        self.is_running = True
        logger.info("🚀 AI驱动自动交易系统启动")
        logger.info(f"💰 初始余额: {self.initial_balance:.2f} USD")
        logger.info(f"⚙️  扫描间隔: {self.config.scan_interval_minutes} 分钟")
        logger.info("🤖 AI将全权决定仓位大小、止损止盈等参数")
        
        # 首次立即执行
        try:
            await self._run_cycle()
        except Exception as e:
            logger.error(f"❌ 执行失败: {e}", exc_info=True)
        
        # 定时循环
        while self.is_running:
            await asyncio.sleep(self.config.scan_interval_minutes * 60)
            if not self.is_running:
                break
            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"❌ 执行失败: {e}", exc_info=True)
    
    def stop(self) -> None:
        """停止自动交易（对应 Go 版本的 Stop()）"""
        self.is_running = False
        logger.info("⏹ 自动交易系统停止")
    
    async def _run_cycle(self) -> None:
        """运行一个交易周期（对应 Go 版本的 runCycle()）"""
        self.call_count += 1
        
        logger.info("\n" + "=" * 70)
        logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - AI决策周期 #{self.call_count}")
        logger.info("=" * 70)
        
        # 创建决策记录（简化版，完整版需要 DecisionRecord 类）
        record: dict[str, Any] = {
            "execution_log": [],
            "success": True,
        }
        
        # 1. 检查是否需要停止交易
        if self.stop_until and datetime.now() < self.stop_until:
            remaining = (self.stop_until - datetime.now()).total_seconds() / 60
            logger.info(f"⏸ 风险控制：暂停交易中，剩余 {remaining:.0f} 分钟")
            record["success"] = False
            record["error_message"] = f"风险控制暂停中，剩余 {remaining:.0f} 分钟"
            self.decision_logger.log(self.id, record)
            return
        
        # 2. 重置日盈亏（每天重置）
        if datetime.now() - self.last_reset_time > timedelta(days=1):
            self.daily_pnl = 0.0
            self.last_reset_time = datetime.now()
            logger.info("📅 日盈亏已重置")
        
        # 3. 收集交易上下文
        try:
            ctx = await self._build_trading_context()
        except Exception as e:
            record["success"] = False
            record["error_message"] = f"构建交易上下文失败: {e}"
            self.decision_logger.log(self.id, record)
            logger.error(f"构建交易上下文失败: {e}", exc_info=True)
            return
        
        # 保存账户状态快照
        record["account_state"] = {
            "total_balance": ctx["account"].total_equity,
            "available_balance": ctx["account"].available_balance,
            "total_unrealized_profit": ctx["account"].total_pnl,
            "position_count": ctx["account"].position_count,
            "margin_used_pct": ctx["account"].margin_used_pct,
        }
        
        # 保存持仓快照
        record["positions"] = []
        for pos in ctx["positions"]:
            record["positions"].append({
                "symbol": pos.symbol,
                "side": pos.side,
                "position_amt": pos.quantity,
                "entry_price": pos.entry_price,
                "mark_price": pos.mark_price,
                "unrealized_profit": pos.unrealized_pnl,
                "leverage": pos.leverage,
                "liquidation_price": pos.liquidation_price,
            })
        
        # 保存候选股票列表
        record["candidate_coins"] = [coin.symbol for coin in ctx["candidate_stocks"]]
        
        logger.info(f"📊 账户净值: {ctx['account'].total_equity:.2f} USD | 可用: {ctx['account'].available_balance:.2f} USD | 持仓: {ctx['account'].position_count}")
        
        # 4. 调用AI获取完整决策
        logger.info("🤖 正在请求AI分析并决策...")
        system_prompt = build_system_prompt(
            ctx["account"].total_equity,
            ctx["btc_eth_leverage"],
            ctx["altcoin_leverage"],
        )
        user_prompt = build_user_prompt(
            current_time=ctx["current_time"],
            call_count=self.call_count,
            runtime_minutes=ctx["runtime_minutes"],
            account=ctx["account"],
            positions=ctx["positions"],
            candidate_stocks=ctx["candidate_stocks"],
            market_data_map=ctx["market_data_map"],
            sharpe_ratio=ctx.get("sharpe_ratio"),
        )
        
        # 调用AI（使用 system + user prompt）
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        ai_response = await self.ai_client.complete(full_prompt)
        
        # 解析决策
        try:
            decision = parse_full_decision_response(
                ai_response,
                ctx["account"].total_equity,
                ctx["btc_eth_leverage"],
                ctx["altcoin_leverage"],
            )
            record["input_prompt"] = user_prompt
            record["cot_trace"] = decision.cot_trace
            if decision.decisions:
                import json as json_lib
                record["decision_json"] = json_lib.dumps([d.__dict__ for d in decision.decisions], indent=2)
        except Exception as e:
            record["success"] = False
            record["error_message"] = f"获取AI决策失败: {e}"
            self.decision_logger.log(self.id, record)
            logger.error(f"获取AI决策失败: {e}", exc_info=True)
            return
        
        # 5. 打印AI思维链
        logger.info("\n" + "-" * 70)
        logger.info("💭 AI思维链分析:")
        logger.info("-" * 70)
        logger.info(decision.cot_trace)
        logger.info("-" * 70 + "\n")
        
        # 6. 打印AI决策
        logger.info(f"📋 AI决策列表 ({len(decision.decisions)} 个):")
        for i, d in enumerate(decision.decisions):
            logger.info(f"  [{i+1}] {d.symbol}: {d.action} - {d.reasoning}")
            if d.action in ("open_long", "open_short"):
                logger.info(f"      杠杆: {d.leverage}x | 仓位: {d.position_size_usd:.2f} USD | 止损: {d.stop_loss:.4f} | 止盈: {d.take_profit:.4f}")
        
        # 7. 对决策排序：确保先平仓后开仓
        sorted_decisions = self._sort_decisions_by_priority(decision.decisions)
        
        logger.info("🔄 执行顺序（已优化）: 先平仓→后开仓")
        for i, d in enumerate(sorted_decisions):
            logger.info(f"  [{i+1}] {d.symbol} {d.action}")
        
        # 8. 执行决策并记录结果
        record["decisions"] = []
        for d in sorted_decisions:
            action_record: dict[str, Any] = {
                "action": d.action,
                "symbol": d.symbol,
                "quantity": 0,
                "leverage": d.leverage,
                "price": 0,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": "",
            }
            
            try:
                await self._execute_decision(d, action_record)
                action_record["success"] = True
                record["execution_log"].append(f"✓ {d.symbol} {d.action} 成功")
                await asyncio.sleep(1)  # 成功执行后短暂延迟
            except Exception as e:
                action_record["error"] = str(e)
                record["execution_log"].append(f"❌ {d.symbol} {d.action} 失败: {e}")
                logger.error(f"❌ 执行决策失败 ({d.symbol} {d.action}): {e}", exc_info=True)
            
            record["decisions"].append(action_record)
        
        # 9. 保存决策记录
        record["timestamp"] = datetime.now().isoformat()
        record["cycle_number"] = self.call_count
        self.decision_logger.log(self.id, record)
    
    async def _build_trading_context(self) -> dict[str, Any]:
        """构建交易上下文（对应 Go 版本的 buildTradingContext()）"""
        # 1. 获取账户信息
        account_dict = await self.trader.get_account()
        balance = account_dict.get("balance", self.initial_balance)
        total_equity = balance
        available_balance = balance
        
        # 2. 获取持仓信息
        positions_dict = await self.trader.get_positions()
        position_infos: list[PositionInfo] = []
        total_margin_used = 0.0
        current_position_keys: set[str] = set()
        
        for pos_dict in positions_dict:
            symbol = pos_dict.get("symbol", "")
            side = pos_dict.get("side", "long")
            entry_price = float(pos_dict.get("entry_price", 0.0))
            mark_price = float(pos_dict.get("mark_price", 0.0))
            quantity = float(pos_dict.get("quantity", 0.0))
            
            # 计算盈亏百分比
            if side == "long":
                pnl_pct = ((mark_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
            else:
                pnl_pct = ((entry_price - mark_price) / entry_price) * 100 if entry_price > 0 else 0.0
            
            leverage = int(pos_dict.get("leverage", 5))
            margin_used = (quantity * mark_price) / leverage if leverage > 0 else 0.0
            total_margin_used += margin_used
            
            # 跟踪持仓首次出现时间
            pos_key = f"{symbol}_{side}"
            current_position_keys.add(pos_key)
            if pos_key not in self.position_first_seen_time:
                self.position_first_seen_time[pos_key] = int(time() * 1000)
            update_time = self.position_first_seen_time[pos_key]
            
            position_infos.append(PositionInfo(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                mark_price=mark_price,
                quantity=quantity,
                leverage=leverage,
                unrealized_pnl=float(pos_dict.get("unrealized_pnl", 0.0)),
                unrealized_pnl_pct=pnl_pct,
                liquidation_price=pos_dict.get("liquidation_price"),
                margin_used=margin_used,
                update_time=update_time,
            ))
        
        # 清理已平仓的持仓记录
        for key in list(self.position_first_seen_time.keys()):
            if key not in current_position_keys:
                del self.position_first_seen_time[key]
        
        # 3. 获取候选股票
        stocks = self.config.stocks or ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        candidate_stocks = [CandidateStock(symbol=s, sources=[]) for s in stocks]
        
        logger.info(f"📋 候选股票池: 总计{len(candidate_stocks)}个候选股票")
        
        # 4. 计算总盈亏和保证金使用率
        total_pnl = total_equity - self.initial_balance
        total_pnl_pct = (total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0.0
        
        margin_used_pct = (total_margin_used / total_equity * 100) if total_equity > 0 else 0.0
        
        # 5. 获取市场数据
        market_data_map: dict[str, dict[str, Any]] = {}
        for stock in candidate_stocks:
            try:
                data = await fetch_stock_with_indicators(stock.symbol, "1min", 120)
                market_data_map[stock.symbol] = {
                    "symbol": stock.symbol,
                    "current_price": float(data["close"].iloc[-1]),
                    "current_ema20": float(data["ema_12"].iloc[-1]) if "ema_12" in data.columns else 0.0,
                    "current_macd": float(data["macd"].iloc[-1]) if "macd" in data.columns else 0.0,
                    "current_rsi7": float(data["rsi"].iloc[-1]) if "rsi" in data.columns else 0.0,
                    "intraday_series": {
                        "mid_prices": data["close"].tail(50).tolist(),
                        "ema20_values": data["ema_12"].tail(50).tolist() if "ema_12" in data.columns else [],
                        "macd_values": data["macd"].tail(50).tolist() if "macd" in data.columns else [],
                        "rsi7_values": data["rsi"].tail(50).tolist() if "rsi" in data.columns else [],
                    },
                }
            except Exception as e:
                logger.warning(f"获取 {stock.symbol} 市场数据失败: {e}")
        
        # 6. 分析历史表现（获取 Sharpe Ratio）
        try:
            performance = self.decision_logger.analyze_performance(self.id, lookback_cycles=20)
            sharpe_ratio = performance.get("sharpe_ratio", 0.0) if performance else None
        except Exception as e:
            logger.warning(f"分析历史表现失败: {e}")
            sharpe_ratio = None
        
        # 7. 构建上下文
        return {
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "runtime_minutes": int((datetime.now() - self.start_time).total_seconds() / 60),
            "account": AccountInfo(
                total_equity=total_equity,
                available_balance=available_balance,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                margin_used=total_margin_used,
                margin_used_pct=margin_used_pct,
                position_count=len(position_infos),
            ),
            "positions": position_infos,
            "candidate_stocks": candidate_stocks,
            "market_data_map": market_data_map,
            "btc_eth_leverage": self.config.btc_eth_leverage,
            "altcoin_leverage": self.config.altcoin_leverage,
            "sharpe_ratio": sharpe_ratio,
        }
    
    def _sort_decisions_by_priority(self, decisions: list[Decision]) -> list[Decision]:
        """对决策排序：确保先平仓后开仓（对应 Go 版本的 sortDecisionsByPriority）"""
        close_decisions = [d for d in decisions if d.action in ("close_long", "close_short")]
        open_decisions = [d for d in decisions if d.action in ("open_long", "open_short")]
        hold_decisions = [d for d in decisions if d.action in ("hold", "wait")]
        return close_decisions + open_decisions + hold_decisions
    
    async def _execute_decision(self, decision: Decision, action_record: dict[str, Any]) -> None:
        """执行AI决策（对应 Go 版本的 executeDecisionWithRecord）"""
        if decision.action == "open_long":
            await self._execute_open_long(decision, action_record)
        elif decision.action == "open_short":
            await self._execute_open_short(decision, action_record)
        elif decision.action == "close_long":
            await self._execute_close_long(decision, action_record)
        elif decision.action == "close_short":
            await self._execute_close_short(decision, action_record)
        elif decision.action in ("hold", "wait"):
            # 无需执行，仅记录
            pass
        else:
            raise ValueError(f"未知的action: {decision.action}")
    
    async def _execute_open_long(self, decision: Decision, action_record: dict[str, Any]) -> None:
        """执行开多仓（对应 Go 版本的 executeOpenLongWithRecord）"""
        logger.info(f"  📈 开多仓: {decision.symbol}")
        
        # ⚠️ 关键：检查是否已有同币种同方向持仓
        positions = await self.trader.get_positions()
        for pos in positions:
            if pos.get("symbol") == decision.symbol and pos.get("side") == "long":
                raise ValueError(f"❌ {decision.symbol} 已有多仓，拒绝开仓以防止仓位叠加超限。如需换仓，请先给出 close_long 决策")
        
        # 获取当前价格（从市场数据获取）
        try:
            data = await fetch_stock_with_indicators(decision.symbol, "1min", 1)
            current_price = float(data["close"].iloc[-1])
        except Exception:
            current_price = 100.0  # 默认价格
        
        # 计算数量
        quantity = int(decision.position_size_usd / current_price) if current_price > 0 else 1
        action_record["quantity"] = quantity
        action_record["price"] = current_price
        
        # 开仓
        order = await self.trader.buy_stock(decision.symbol, quantity)
        action_record["order_id"] = order.get("order_id", order.get("orderId", 0))
        logger.info(f"  ✓ 开仓成功，订单ID: {action_record['order_id']}, 数量: {quantity}")
        
        # 记录开仓时间
        pos_key = f"{decision.symbol}_long"
        self.position_first_seen_time[pos_key] = int(time() * 1000)
    
    async def _execute_open_short(self, decision: Decision, action_record: dict[str, Any]) -> None:
        """执行开空仓（对应 Go 版本的 executeOpenShortWithRecord）"""
        logger.info(f"  📉 开空仓: {decision.symbol}")
        
        # ⚠️ 关键：检查是否已有同币种同方向持仓
        positions = await self.trader.get_positions()
        for pos in positions:
            if pos.get("symbol") == decision.symbol and pos.get("side") == "short":
                raise ValueError(f"❌ {decision.symbol} 已有空仓，拒绝开仓以防止仓位叠加超限。如需换仓，请先给出 close_short 决策")
        
        # 获取当前价格
        try:
            data = await fetch_stock_with_indicators(decision.symbol, "1min", 1)
            current_price = float(data["close"].iloc[-1])
        except Exception:
            current_price = 100.0  # 默认价格
        
        # 计算数量
        quantity = int(decision.position_size_usd / current_price) if current_price > 0 else 1
        action_record["quantity"] = quantity
        action_record["price"] = current_price
        
        # 开空仓
        order = await self.trader.short_stock(decision.symbol, quantity)
        action_record["order_id"] = order.get("order_id", order.get("orderId", 0))
        logger.info(f"  ✓ 开仓成功，订单ID: {action_record['order_id']}, 数量: {quantity}")
        
        # 记录开仓时间
        pos_key = f"{decision.symbol}_short"
        self.position_first_seen_time[pos_key] = int(time() * 1000)
    
    async def _execute_close_long(self, decision: Decision, action_record: dict[str, Any]) -> None:
        """执行平多仓（对应 Go 版本的 executeCloseLongWithRecord）"""
        logger.info(f"  🔄 平多仓: {decision.symbol}")
        
        # 获取当前价格
        try:
            data = await fetch_stock_with_indicators(decision.symbol, "1min", 1)
            current_price = float(data["close"].iloc[-1])
        except Exception:
            current_price = 100.0  # 默认价格
        action_record["price"] = current_price
        
        # 平仓（0 = 全部平仓）
        order = await self.trader.sell_stock(decision.symbol, 0)
        action_record["order_id"] = order.get("order_id", order.get("orderId", 0))
        logger.info(f"  ✓ 平仓成功")
    
    async def _execute_close_short(self, decision: Decision, action_record: dict[str, Any]) -> None:
        """执行平空仓（对应 Go 版本的 executeCloseShortWithRecord）"""
        logger.info(f"  🔄 平空仓: {decision.symbol}")
        
        # 获取当前价格
        try:
            data = await fetch_stock_with_indicators(decision.symbol, "1min", 1)
            current_price = float(data["close"].iloc[-1])
        except Exception:
            current_price = 100.0  # 默认价格
        action_record["price"] = current_price
        
        # 平空仓（0 = 全部平仓）
        order = await self.trader.cover_short(decision.symbol, 0)
        action_record["order_id"] = order.get("order_id", order.get("orderId", 0))
        logger.info(f"  ✓ 平仓成功")
    
    # === 查询接口（供API使用）===
    
    async def get_account_info(self) -> dict[str, Any]:
        """获取账户信息"""
        account = await self.trader.get_account()
        positions = await self.trader.get_positions()
        total_equity = account.get("balance", self.initial_balance)
        total_pnl = total_equity - self.initial_balance
        total_pnl_pct = (total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0.0
        
        return {
            "total_equity": total_equity,
            "available_balance": account.get("balance", 0.0),
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "position_count": len(positions),
            "margin_used_pct": 0.0,  # TODO: 计算实际保证金使用率
            "initial_balance": self.initial_balance,
        }
    
    def get_status(self) -> dict[str, Any]:
        """获取运行状态"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat(),
            "runtime_minutes": int((datetime.now() - self.start_time).total_seconds() / 60),
            "call_count": self.call_count,
        }
    
    def get_id(self) -> str:
        return self.id
    
    def get_name(self) -> str:
        return self.name
    
    def get_ai_model(self) -> str:
        return self.ai_model

