"""
A股交易规则（单例模式）
实现 T+1、涨跌停限制、持仓限制等 A 股特有规则
"""
from typing import Dict, Any, Tuple, Optional
from datetime import date, timedelta
from loguru import logger


class AShareTradingRules:
    """
    A股交易规则
    
    规则：
    1. T+1 规则：当天买入，下一个交易日才能卖出
    2. 涨跌停限制：主板 ±10%，科创板/创业板 ±20%
    3. 持仓限制：单只股票持仓不超过投资组合的一定比例
    4. 最小交易单位：100股（1手）的整数倍
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化（仅执行一次）"""
        if self._initialized:
            return
        
        # 涨跌停幅度（按市场/板块）
        self.limit_pct = {
            'SH': 0.10,   # 上海主板 ±10%
            'SZ': 0.10,   # 深圳主板 ±10%
            'BJ': 0.10,   # 北京交易所 ±10%
            'KCB': 0.20,  # 科创板 ±20%
            'CYB': 0.20,  # 创业板 ±20%
        }
        
        # 持仓限制
        self.max_position_pct = 0.10  # 单只股票最大持仓比例（10%）
        
        self._initialized = True
        logger.info("✓ A股交易规则初始化完成")
    
    @classmethod
    def get_instance(cls) -> 'AShareTradingRules':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def apply_t_plus_one(self, 
                        signal_date: date, 
                        execution_date: date, 
                        calendar: Optional[Any] = None) -> Tuple[bool, str]:
        """
        应用 T+1 规则：当天买入，下一个交易日才能卖出
        
        Args:
            signal_date: 信号日期（买入日期）
            execution_date: 执行日期（卖出日期）
            calendar: 交易日历对象（用于计算下一个交易日）
            
        Returns:
            Tuple[bool, str]: (是否可以执行, 原因)
        """
        if signal_date == execution_date:
            return (False, "T+1 rule: cannot sell on the same day as purchase")
        
        # 如果有交易日历，计算下一个交易日
        if calendar:
            next_trading_day = calendar.get_next_trading_day(signal_date)
            if execution_date < next_trading_day:
                return (False, f"T+1 rule: can only sell on or after {next_trading_day}")
        else:
            # 简化实现：假设明天是交易日
            expected_next_day = signal_date + timedelta(days=1)
            if execution_date < expected_next_day:
                return (False, f"T+1 rule: can only sell on or after {expected_next_day}")
        
        return (True, "")
    
    def apply_price_limit(self, 
                        order_price: float, 
                        prev_close: float, 
                        stock_code: str = "sh.600000") -> Tuple[float, str]:
        """
        应用涨跌停限制：订单价格不能超过涨跌停价
        
        Args:
            order_price: 订单价格
            prev_close: 昨日收盘价
            stock_code: 股票代码（用于判断涨跌停幅度）
            
        Returns:
            Tuple[float, str]: (调整后的价格, 原因)
        """
        # 判断涨跌停幅度
        limit_pct = self._get_limit_pct(stock_code)
        
        # 计算涨跌停价
        upper_limit = round(prev_close * (1 + limit_pct), 2)
        lower_limit = round(prev_close * (1 - limit_pct), 2)
        
        # 调整价格
        if order_price > upper_limit:
            return (upper_limit, f"Price limit: adjusted from {order_price:.2f} to {upper_limit:.2f} (up limit)")
        elif order_price < lower_limit:
            return (lower_limit, f"Price limit: adjusted from {order_price:.2f} to {lower_limit:.2f} (down limit)")
        
        return (order_price, "")
    
    def check_position_limit(self, 
                          stock_code: str, 
                          position_value: float, 
                          total_value: float, 
                          max_position_pct: Optional[float] = None) -> Tuple[bool, str]:
        """
        检查持仓限制：单只股票持仓不超过投资组合的一定比例
        
        Args:
            stock_code: 股票代码
            position_value: 持仓市值
            total_value: 投资组合总市值
            max_position_pct: 最大持仓比例（None 则使用默认值）
            
        Returns:
            Tuple[bool, str]: (是否通过, 原因)
        """
        if total_value <= 0:
            return (False, "Total portfolio value is zero or negative")
        
        position_pct = position_value / total_value
        limit = max_position_pct or self.max_position_pct
        
        if position_pct > limit:
            return (False, f"Position limit exceeded: {position_pct:.2%} > {limit:.2%}")
        
        return (True, "")
    
    def check_min_trading_unit(self, quantity: int) -> Tuple[bool, str]:
        """
        检查最小交易单位：必须是 100股（1手）的整数倍
        
        Args:
            quantity: 交易数量
            
        Returns:
            Tuple[bool, str]: (是否通过, 原因)
        """
        if quantity % 100!= 0:
            # 调整到最近的 100 的整数倍
            adjusted_quantity = (quantity // 100) * 100
            return (False, f"Min trading unit: {quantity} adjusted to {adjusted_quantity} (must be multiple of 100)")
        
        return (True, "")
    
    def validate_order(self, 
                     order: Dict[str, Any], 
                     portfolio: Any, 
                     calendar: Optional[Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        验证订单是否合法（综合检查）
        
        Args:
            order: 订单信息
                {
                    "stock_code": "sh.600000",
                    "action": "buy" or "sell",
                    "quantity": 100,
                    "price": 10.5,
                    "signal_date": date,
                    "execution_date": date
                }
            portfolio: 投资组合对象
            calendar: 交易日历对象
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否有效, 原因, 调整后的订单)
        """
        adjusted_order = order.copy()
        
        # 检查 1: T+1 规则（卖出时检查）
        if order["action"] == "sell":
            is_valid, reason = self.apply_t_plus_one(
                order.get("signal_date"),
                order.get("execution_date"),
                calendar
            )
            if not is_valid:
                return (False, reason, None)
        
        # 检查 2: 涨跌停限制
        if "price" in order and "prev_close" in order:
            adjusted_price, reason = self.apply_price_limit(
                order["price"],
                order["prev_close"],
                order.get("stock_code", "sh.600000")
            )
            if adjusted_price!= order["price"]:
                logger.warning(f"Order price adjusted: {reason}")
                adjusted_order["price"] = adjusted_price
        
        # 检查 3: 最小交易单位
        is_valid, reason = self.check_min_trading_unit(order["quantity"])
        if not is_valid:
            adjusted_quantity = (order["quantity"] // 100) * 100
            if adjusted_quantity > 0:
                adjusted_order["quantity"] = adjusted_quantity
                logger.warning(f"Order quantity adjusted: {reason}")
            else:
                return (False, "Order quantity too small after adjustment", None)
        
        # 检查 4: 持仓限制（买入时检查）
        if order["action"] == "buy" and portfolio:
            # 计算买入后的持仓
            estimated_cost = order["quantity"] * adjusted_order["price"]
            position_value = portfolio.positions.get(order["stock_code"], 0) * adjusted_order["price"]
            total_value = portfolio.get_total_value()
            
            is_valid, reason = self.check_position_limit(
                order["stock_code"],
                position_value + estimated_cost,
                total_value + estimated_cost  # 简化：假设所有资金都用于买入
            )
            if not is_valid:
                logger.warning(f"Position limit check: {reason}")
                # 不阻止订单，只记录警告
        
        return (True, "Order validated", adjusted_order)
    
    def _get_limit_pct(self, stock_code: str) -> float:
        """
        获取涨跌停幅度
        
        Args:
            stock_code: 股票代码（格式: sh.600000）
            
        Returns:
            float: 涨跌停幅度（0.1 = 10%）
        """
        # 判断市场
        if stock_code.startswith('sh.'):
            market = 'SH'
            # TODO: 判断是否为科创板（股票代码 688 开头）
            if stock_code.startswith('sh.688'):
                market = 'KCB'
        elif stock_code.startswith('sz.'):
            market = 'SZ'
            # TODO: 判断是否为创业板（股票代码 300 开头）
            if stock_code.startswith('sz.300') or stock_code.startswith('sz.301'):
                market = 'CYB'
        elif stock_code.startswith('bj.'):
            market = 'BJ'
        else:
            market = 'SH'  # 默认
        
        return self.limit_pct.get(market, 0.10)
    
    def set_max_position_pct(self, pct: float) -> None:
        """
        设置最大持仓比例
        
        Args:
            pct: 持仓比例（0.1 = 10%）
        """
        if 0 < pct <= 1:
            self.max_position_pct = pct
            logger.info(f"最大持仓比例设置为: {pct:.2%}")
        else:
            logger.error(f"无效的持仓比例: {pct}")
    
    def set_limit_pct(self, market: str, pct: float) -> None:
        """
        设置涨跌停幅度
        
        Args:
            market: 市场代码（'SH', 'SZ', 'KCB', 'CYB', 'BJ'）
            pct: 涨跌停幅度（0.1 = 10%）
        """
        if 0 < pct <= 1:
            self.limit_pct[market] = pct
            logger.info(f"{market} 涨跌停幅度设置为: {pct:.2%}")
        else:
            logger.error(f"无效的涨跌停幅度: {pct}")
