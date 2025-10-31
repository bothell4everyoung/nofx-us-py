from __future__ import annotations

from typing import Any, Dict, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json
import re


@dataclass
class PositionInfo:
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    mark_price: float
    quantity: float
    leverage: int
    unrealized_pnl: float
    unrealized_pnl_pct: float
    liquidation_price: float | None
    margin_used: float
    update_time: int = 0  # 持仓更新时间戳（毫秒）


@dataclass
class AccountInfo:
    total_equity: float
    available_balance: float
    total_pnl: float
    total_pnl_pct: float
    margin_used: float
    margin_used_pct: float
    position_count: int


@dataclass
class CandidateStock:
    symbol: str
    sources: list[str] = field(default_factory=list)  # 来源标记


@dataclass
class Decision:
    symbol: str
    action: str  # "open_long", "open_short", "close_long", "close_short", "hold", "wait"
    leverage: int = 0
    position_size_usd: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    confidence: int = 0  # 0-100
    risk_usd: float = 0.0
    reasoning: str = ""


@dataclass
class FullDecision:
    user_prompt: str
    cot_trace: str
    decisions: list[Decision]
    timestamp: datetime


def build_system_prompt(account_equity: float, btc_eth_leverage: int, altcoin_leverage: int) -> str:
    """构建 System Prompt（固定规则，可缓存）- 完整迁移自原始 Go 版本
    
    核心知识产权：最大化夏普比率的交易策略
    """
    lines = []
    
    # === 核心使命 ===
    lines.append("你是专业的美国股票/期权交易AI，在美股市场进行自主交易。\n")
    lines.append("# 🎯 核心目标\n\n")
    lines.append("**最大化夏普比率（Sharpe Ratio）**\n\n")
    lines.append("夏普比率 = 平均收益 / 收益波动率\n\n")
    lines.append("**这意味着**：\n")
    lines.append("- ✅ 高质量交易（高胜率、大盈亏比）→ 提升夏普\n")
    lines.append("- ✅ 稳定收益、控制回撤 → 提升夏普\n")
    lines.append("- ✅ 耐心持仓、让利润奔跑 → 提升夏普\n")
    lines.append("- ❌ 频繁交易、小盈小亏 → 增加波动，严重降低夏普\n")
    lines.append("- ❌ 过度交易、手续费损耗 → 直接亏损\n")
    lines.append("- ❌ 过早平仓、频繁进出 → 错失大行情\n\n")
    lines.append("**关键认知**: 系统每3分钟扫描一次，但不意味着每次都要交易！\n")
    lines.append("大多数时候应该是 `wait` 或 `hold`，只在极佳机会时才开仓。\n\n")
    
    # === 硬约束（风险控制）===
    lines.append("# ⚖️ 硬约束（风险控制）\n\n")
    lines.append("1. **风险回报比**: 必须 ≥ 1:3（冒1%风险，赚3%+收益）\n")
    lines.append("2. **最多持仓**: 3个股票（质量>数量）\n")
    lines.append(f"3. **单股仓位**: 普通股票 {account_equity*0.8:.0f}-{account_equity*1.5:.0f} USD({altcoin_leverage}x杠杆) | 大盘股 {account_equity*5:.0f}-{account_equity*10:.0f} USD({btc_eth_leverage}x杠杆)\n")
    lines.append("4. **保证金**: 总使用率 ≤ 90%\n\n")
    
    # === 做空激励 ===
    lines.append("# 📉 做多做空平衡\n\n")
    lines.append("**重要**: 下跌趋势做空的利润 = 上涨趋势做多的利润\n\n")
    lines.append("- 上涨趋势 → 做多\n")
    lines.append("- 下跌趋势 → 做空\n")
    lines.append("- 震荡市场 → 观望\n\n")
    lines.append("**不要有做多偏见！做空是你的核心工具之一**\n\n")
    
    # === 交易频率认知 ===
    lines.append("# ⏱️ 交易频率认知\n\n")
    lines.append("**量化标准**:\n")
    lines.append("- 优秀交易员：每天2-4笔 = 每小时0.1-0.2笔\n")
    lines.append("- 过度交易：每小时>2笔 = 严重问题\n")
    lines.append("- 最佳节奏：开仓后持有至少30-60分钟\n\n")
    lines.append("**自查**:\n")
    lines.append("如果你发现自己每个周期都在交易 → 说明标准太低\n")
    lines.append("如果你发现持仓<30分钟就平仓 → 说明太急躁\n\n")
    
    # === 开仓信号强度 ===
    lines.append("# 🎯 开仓标准（严格）\n\n")
    lines.append("只在**强信号**时开仓，不确定就观望。\n\n")
    lines.append("**你拥有的完整数据**：\n")
    lines.append("- 📊 **原始序列**：价格序列 + 技术指标序列\n")
    lines.append("- 📈 **技术序列**：EMA20序列、MACD序列、RSI7序列、RSI14序列\n")
    lines.append("- 💰 **资金序列**：成交量序列、持仓量序列\n")
    lines.append("- 🎯 **筛选标记**：评分 / Top排名（如果有标注）\n\n")
    lines.append("**分析方法**（完全由你自主决定）：\n")
    lines.append("- 自由运用序列数据，你可以做但不限于趋势分析、形态识别、支撑阻力、技术阻力位、斐波那契、波动带计算\n")
    lines.append("- 多维度交叉验证（价格+量+指标+序列形态）\n")
    lines.append("- 用你认为最有效的方法发现高确定性机会\n")
    lines.append("- 综合信心度 ≥ 75 才开仓\n\n")
    lines.append("**避免低质量信号**：\n")
    lines.append("- 单一维度（只看一个指标）\n")
    lines.append("- 相互矛盾（涨但量萎缩）\n")
    lines.append("- 横盘震荡\n")
    lines.append("- 刚平仓不久（<15分钟）\n\n")
    
    # === 夏普比率自我进化 ===
    lines.append("# 🧬 夏普比率自我进化\n\n")
    lines.append("每次你会收到**夏普比率**作为绩效反馈（周期级别）：\n\n")
    lines.append("**夏普比率 < -0.5** (持续亏损):\n")
    lines.append("  → 🛑 停止交易，连续观望至少6个周期（18分钟）\n")
    lines.append("  → 🔍 深度反思：\n")
    lines.append("     • 交易频率过高？（每小时>2次就是过度）\n")
    lines.append("     • 持仓时间过短？（<30分钟就是过早平仓）\n")
    lines.append("     • 信号强度不足？（信心度<75）\n")
    lines.append("     • 是否在做空？（单边做多是错误的）\n\n")
    lines.append("**夏普比率 -0.5 ~ 0** (轻微亏损):\n")
    lines.append("  → ⚠️ 严格控制：只做信心度>80的交易\n")
    lines.append("  → 减少交易频率：每小时最多1笔新开仓\n")
    lines.append("  → 耐心持仓：至少持有30分钟以上\n\n")
    lines.append("**夏普比率 0 ~ 0.7** (正收益):\n")
    lines.append("  → ✅ 维持当前策略\n\n")
    lines.append("**夏普比率 > 0.7** (优异表现):\n")
    lines.append("  → 🚀 可适度扩大仓位\n\n")
    lines.append("**关键**: 夏普比率是唯一指标，它会自然惩罚频繁交易和过度进出。\n\n")
    
    # === 决策流程 ===
    lines.append("# 📋 决策流程\n\n")
    lines.append("1. **分析夏普比率**: 当前策略是否有效？需要调整吗？\n")
    lines.append("2. **评估持仓**: 趋势是否改变？是否该止盈/止损？\n")
    lines.append("3. **寻找新机会**: 有强信号吗？多空机会？\n")
    lines.append("4. **输出决策**: 思维链分析 + JSON\n\n")
    
    # === 输出格式 ===
    lines.append("# 📤 输出格式\n\n")
    lines.append("**第一步: 思维链（纯文本）**\n")
    lines.append("简洁分析你的思考过程\n\n")
    lines.append("**第二步: JSON决策数组**\n\n")
    lines.append("```json\n[\n")
    lines.append(f'  {{"symbol": "AAPL", "action": "open_long", "leverage": {altcoin_leverage}, "position_size_usd": {account_equity*0.8:.0f}, "stop_loss": 150.0, "take_profit": 165.0, "confidence": 85, "risk_usd": 300, "reasoning": "上涨趋势+MACD金叉"}},\n')
    lines.append('  {"symbol": "TSLA", "action": "close_long", "reasoning": "止盈离场"}\n')
    lines.append("]\n```\n\n")
    lines.append("**字段说明**:\n")
    lines.append("- `action`: open_long | open_short | close_long | close_short | hold | wait\n")
    lines.append("- `confidence`: 0-100（开仓建议≥75）\n")
    lines.append("- 开仓时必填: leverage, position_size_usd, stop_loss, take_profit, confidence, risk_usd, reasoning\n\n")
    
    # === 关键提醒 ===
    lines.append("---\n\n")
    lines.append("**记住**: \n")
    lines.append("- 目标是夏普比率，不是交易频率\n")
    lines.append("- 做空 = 做多，都是赚钱工具\n")
    lines.append("- 宁可错过，不做低质量交易\n")
    lines.append("- 风险回报比1:3是底线\n")
    
    return "".join(lines)


def format_market_data(data: dict[str, Any]) -> str:
    """格式化市场数据（对应 Go 版本的 Format 函数）
    
    Args:
        data: 市场数据字典，包含 price, ema20, macd, rsi, volume 等字段
    """
    lines = []
    
    price = data.get("current_price", 0.0)
    ema20 = data.get("current_ema20", 0.0)
    macd = data.get("current_macd", 0.0)
    rsi7 = data.get("current_rsi7", 0.0)
    
    lines.append(f"current_price = {price:.2f}, current_ema20 = {ema20:.3f}, current_macd = {macd:.3f}, current_rsi (7 period) = {rsi7:.3f}\n\n")
    
    symbol = data.get("symbol", "")
    if symbol:
        lines.append(f"In addition, here is the latest {symbol} data:\n\n")
    
    # 日内序列（如果存在）
    if "intraday_series" in data:
        series = data["intraday_series"]
        lines.append("Intraday series (1-minute intervals, oldest → latest):\n\n")
        
        if "mid_prices" in series:
            prices = series["mid_prices"]
            if prices:
                prices_str = ", ".join(f"{p:.3f}" for p in prices)
                lines.append(f"Mid prices: [{prices_str}]\n\n")
        
        if "ema20_values" in series:
            ema_values = series["ema20_values"]
            if ema_values:
                ema_str = ", ".join(f"{e:.3f}" for e in ema_values)
                lines.append(f"EMA indicators (20-period): [{ema_str}]\n\n")
        
        if "macd_values" in series:
            macd_values = series["macd_values"]
            if macd_values:
                macd_str = ", ".join(f"{m:.3f}" for m in macd_values)
                lines.append(f"MACD indicators: [{macd_str}]\n\n")
        
        if "rsi7_values" in series:
            rsi7_values = series["rsi7_values"]
            if rsi7_values:
                rsi_str = ", ".join(f"{r:.3f}" for r in rsi7_values)
                lines.append(f"RSI indicators (7-Period): [{rsi_str}]\n\n")
        
        if "rsi14_values" in series:
            rsi14_values = series["rsi14_values"]
            if rsi14_values:
                rsi_str = ", ".join(f"{r:.3f}" for r in rsi14_values)
                lines.append(f"RSI indicators (14-Period): [{rsi_str}]\n\n")
    
    # 长期上下文（如果存在）
    if "longer_term_context" in data:
        context = data["longer_term_context"]
        lines.append("Longer-term context (daily timeframe):\n\n")
        
        ema20_lt = context.get("ema20", 0.0)
        ema50_lt = context.get("ema50", 0.0)
        lines.append(f"20-Period EMA: {ema20_lt:.3f} vs. 50-Period EMA: {ema50_lt:.3f}\n\n")
        
        volume = context.get("current_volume", 0.0)
        avg_volume = context.get("average_volume", 0.0)
        lines.append(f"Current Volume: {volume:.3f} vs. Average Volume: {avg_volume:.3f}\n\n")
    
    return "".join(lines)


def build_user_prompt(
    current_time: str,
    call_count: int,
    runtime_minutes: int,
    account: AccountInfo,
    positions: list[PositionInfo],
    candidate_stocks: list[CandidateStock],
    market_data_map: dict[str, dict[str, Any]],
    sharpe_ratio: float | None = None,
) -> str:
    """构建 User Prompt（动态数据）- 完整迁移自原始 Go 版本"""
    lines = []
    
    # 系统状态
    lines.append(f"**时间**: {current_time} | **周期**: #{call_count} | **运行**: {runtime_minutes}分钟\n\n")
    
    # 账户
    lines.append(f"**账户**: 净值{account.total_equity:.2f} | 余额{account.available_balance:.2f} ({account.available_balance/account.total_equity*100:.1f}%) | 盈亏{account.total_pnl_pct:+.2f}% | 保证金{account.margin_used_pct:.1f}% | 持仓{account.position_count}个\n\n")
    
    # 持仓（完整市场数据）
    if positions:
        lines.append("## 当前持仓\n")
        for i, pos in enumerate(positions):
            # 计算持仓时长
            holding_duration = ""
            if pos.update_time > 0:
                from time import time
                duration_ms = int(time() * 1000) - pos.update_time
                duration_min = duration_ms // (1000 * 60)
                if duration_min < 60:
                    holding_duration = f" | 持仓时长{duration_min}分钟"
                else:
                    duration_hour = duration_min // 60
                    duration_min_remainder = duration_min % 60
                    holding_duration = f" | 持仓时长{duration_hour}小时{duration_min_remainder}分钟"
            
            side_upper = pos.side.upper()
            lines.append(f"{i+1}. {pos.symbol} {side_upper} | 入场价{pos.entry_price:.4f} 当前价{pos.mark_price:.4f} | 盈亏{pos.unrealized_pnl_pct:+.2f}% | 杠杆{pos.leverage}x | 保证金{pos.margin_used:.0f}")
            if pos.liquidation_price:
                lines.append(f" | 强平价{pos.liquidation_price:.4f}")
            lines.append(f"{holding_duration}\n\n")
            
            # 使用FormatMarketData输出完整市场数据
            if pos.symbol in market_data_map:
                lines.append(format_market_data(market_data_map[pos.symbol]))
                lines.append("\n")
    else:
        lines.append("**当前持仓**: 无\n\n")
    
    # 候选股票（完整市场数据）
    displayed_count = 0
    for stock in candidate_stocks:
        if stock.symbol not in market_data_map:
            continue
        displayed_count += 1
        
        source_tags = ""
        if len(stock.sources) > 1:
            source_tags = " (双重信号)"
        elif stock.sources and stock.sources[0] == "oi_top":
            source_tags = " (持仓增长)"
        
        lines.append(f"### {displayed_count}. {stock.symbol}{source_tags}\n\n")
        lines.append(format_market_data(market_data_map[stock.symbol]))
        lines.append("\n")
    
    # 夏普比率
    if sharpe_ratio is not None:
        lines.append(f"## 📊 夏普比率: {sharpe_ratio:.2f}\n\n")
    
    lines.append("---\n\n")
    lines.append("现在请分析并输出决策（思维链 + JSON）\n")
    
    return "".join(lines)


def extract_cot_trace(response: str) -> str:
    """提取思维链分析（对应 Go 版本的 extractCoTTrace）"""
    json_start = response.find("[")
    if json_start > 0:
        return response[:json_start].strip()
    return response.strip()


def extract_decisions(response: str) -> list[Decision]:
    """提取JSON决策列表（对应 Go 版本的 extractDecisions）"""
    # 查找JSON数组起始
    array_start = response.find("[")
    if array_start == -1:
        raise ValueError("无法找到JSON数组起始")
    
    # 查找匹配的右括号
    depth = 0
    array_end = -1
    for i in range(array_start, len(response)):
        if response[i] == '[':
            depth += 1
        elif response[i] == ']':
            depth -= 1
            if depth == 0:
                array_end = i
                break
    
    if array_end == -1:
        raise ValueError("无法找到JSON数组结束")
    
    json_content = response[array_start:array_end + 1].strip()
    
    # 修复常见的JSON格式错误：缺少引号的字段值
    json_content = fix_missing_quotes(json_content)
    
    # 解析JSON
    try:
        decisions_data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {e}\nJSON内容: {json_content}")
    
    decisions = []
    for d in decisions_data:
        decision = Decision(
            symbol=d.get("symbol", ""),
            action=d.get("action", "hold"),
            leverage=d.get("leverage", 0),
            position_size_usd=d.get("position_size_usd", 0.0),
            stop_loss=d.get("stop_loss", 0.0),
            take_profit=d.get("take_profit", 0.0),
            confidence=d.get("confidence", 0),
            risk_usd=d.get("risk_usd", 0.0),
            reasoning=d.get("reasoning", ""),
        )
        decisions.append(decision)
    
    return decisions


def fix_missing_quotes(json_str: str) -> str:
    """替换中文引号为英文引号（避免输入法自动转换）"""
    json_str = json_str.replace("\u201c", '"')  # "
    json_str = json_str.replace("\u201d", '"')  # "
    json_str = json_str.replace("\u2018", "'")  # '
    json_str = json_str.replace("\u2019", "'")  # '
    return json_str


def validate_decision(
    decision: Decision,
    account_equity: float,
    btc_eth_leverage: int,
    altcoin_leverage: int,
) -> None:
    """验证单个决策的有效性（对应 Go 版本的 validateDecision）"""
    valid_actions = {
        "open_long", "open_short", "close_long", "close_short", "hold", "wait"
    }
    
    if decision.action not in valid_actions:
        raise ValueError(f"无效的action: {decision.action}")
    
    # 开仓操作必须提供完整参数
    if decision.action in ("open_long", "open_short"):
        # 根据股票类型使用配置的杠杆上限
        max_leverage = altcoin_leverage
        max_position_value = account_equity * 1.5
        if decision.symbol in ("AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"):
            max_leverage = btc_eth_leverage
            max_position_value = account_equity * 10
        
        if decision.leverage <= 0 or decision.leverage > max_leverage:
            raise ValueError(f"杠杆必须在1-{max_leverage}之间（{decision.symbol}，当前配置上限{max_leverage}倍）: {decision.leverage}")
        
        if decision.position_size_usd <= 0:
            raise ValueError(f"仓位大小必须大于0: {decision.position_size_usd:.2f}")
        
        # 验证仓位价值上限（加1%容差）
        tolerance = max_position_value * 0.01
        if decision.position_size_usd > max_position_value + tolerance:
            raise ValueError(f"单股仓位价值不能超过{max_position_value:.0f} USD，实际: {decision.position_size_usd:.0f}")
        
        if decision.stop_loss <= 0 or decision.take_profit <= 0:
            raise ValueError("止损和止盈必须大于0")
        
        # 验证止损止盈的合理性
        if decision.action == "open_long":
            if decision.stop_loss >= decision.take_profit:
                raise ValueError("做多时止损价必须小于止盈价")
        else:
            if decision.stop_loss <= decision.take_profit:
                raise ValueError("做空时止损价必须大于止盈价")
        
        # 验证风险回报比（必须≥1:3）
        # 计算入场价（假设当前市价）
        if decision.action == "open_long":
            entry_price = decision.stop_loss + (decision.take_profit - decision.stop_loss) * 0.2
            risk_percent = (entry_price - decision.stop_loss) / entry_price * 100
            reward_percent = (decision.take_profit - entry_price) / entry_price * 100
        else:
            entry_price = decision.stop_loss - (decision.stop_loss - decision.take_profit) * 0.2
            risk_percent = (decision.stop_loss - entry_price) / entry_price * 100
            reward_percent = (entry_price - decision.take_profit) / entry_price * 100
        
        if risk_percent > 0:
            risk_reward_ratio = reward_percent / risk_percent
            # 硬约束：风险回报比必须≥3.0
            if risk_reward_ratio < 3.0:
                raise ValueError(
                    f"风险回报比过低({risk_reward_ratio:.2f}:1)，必须≥3.0:1 "
                    f"[风险:{risk_percent:.2f}% 收益:{reward_percent:.2f}%] "
                    f"[止损:{decision.stop_loss:.2f} 止盈:{decision.take_profit:.2f}]"
                )


def parse_full_decision_response(
    ai_response: str,
    account_equity: float,
    btc_eth_leverage: int,
    altcoin_leverage: int,
) -> FullDecision:
    """解析AI的完整决策响应（对应 Go 版本的 parseFullDecisionResponse）"""
    # 1. 提取思维链
    cot_trace = extract_cot_trace(ai_response)
    
    # 2. 提取JSON决策列表
    try:
        decisions = extract_decisions(ai_response)
    except Exception as e:
        return FullDecision(
            user_prompt="",
            cot_trace=cot_trace,
            decisions=[],
            timestamp=datetime.now(),
        )
    
    # 3. 验证决策
    for decision in decisions:
        try:
            validate_decision(decision, account_equity, btc_eth_leverage, altcoin_leverage)
        except ValueError as e:
            # 验证失败时返回带错误的决策
            pass
    
    return FullDecision(
        user_prompt="",  # 由调用者填充
        cot_trace=cot_trace,
        decisions=decisions,
        timestamp=datetime.now(),
    )


def parse_decision(response_text: str) -> Dict[str, Any]:
    """简单的决策解析函数（兼容层，用于简化调用）
    
    将AI响应解析为简单的字典格式，兼容旧的调用方式。
    """
    try:
        data = json.loads(response_text)
    except Exception:
        # 尝试从完整响应中提取JSON数组
        try:
            decisions = extract_decisions(response_text)
            if decisions:
                d = decisions[0]
                return {
                    "action": "buy" if d.action == "open_long" else ("sell" if d.action == "close_long" else "hold"),
                    "symbol": d.symbol,
                    "quantity": int(d.position_size_usd / 100.0) if d.position_size_usd > 0 else 1,
                }
        except Exception:
            pass
        return {"action": "hold"}
    
    action = str(data.get("action", "hold")).lower()
    if action not in {"buy", "sell", "hold", "open_long", "open_short", "close_long", "close_short", "wait"}:
        action = "hold"
    
    # 映射到简单格式
    if action in ("open_long", "buy"):
        return {
            "action": "buy",
            "symbol": data.get("symbol", ""),
            "quantity": int(data.get("quantity", data.get("position_size_usd", 0) / 100.0)),
        }
    elif action in ("close_long", "sell"):
        return {
            "action": "sell",
            "symbol": data.get("symbol", ""),
            "quantity": int(data.get("quantity", 1)),
        }
    
    return {"action": "hold"}
