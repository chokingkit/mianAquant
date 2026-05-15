"""
订单执行器
负责执行交易订单，更新投资组合
"""
from typing import Dict, Any, Optional, List
from datetime import date
from loguru import logger
import pandas as pd


class OrderExecutor:
    """
    订单执行器
    
    负责：
    1. 执行买入订单
    2. 执行卖出订单
    3. 更新投资组合
    4. 记录交易记录
    """
    
    def __init__(self, commission: float = 0.0003, slippage: float = 0.001):
        """
        初始化执行器
        
        Args:
            commission: 佣金费率（默认 0.0003 = 万3）
            slippage: 滑点（默认 0.001 = 0.1%）
        """
        self.commission = commission
        self.slippage = slippage
        self.logger = logger.bind(module="OrderExecutor")
        self.logger.info(f"✓ 订单执行器初始化完成 (commission={commission}, slippage={slippage})")
    
    def execute_order(self, 
                     order: Dict[str, Any], 
                     portfolio: Any, 
                     commission: Optional[float] = None,
                     slippage: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        执行订单
        
        Args:
            order: 订单信息
                {
                    "stock_code": "sh.600000",
                    "action": "buy" or "sell",
                    "quantity": 100,
                    "price": 10.5,
                    "reason": "MA cross"  # 可选
                }
            portfolio: 投资组合对象
            commission: 佣金费率（None 则使用默认值）
            slippage: 滑点（None 则使用默认值）
            
        Returns:
            Dict: 交易记录（None 表示执行失败）
                {
                    "stock_code": "sh.600000",
                    "action": "buy",
                    "quantity": 100,
                    "price": 10.5,
                    "amount": 1050.0,  # 成交金额
                    "commission": 0.315,  # 佣金
                    "slippage": 1.05,    # 滑点成本
                    "timestamp": date
                }
        """
        action = order.get("action", "").lower()
        stock_code = order.get("stock_code")
        quantity = order.get("quantity", 0)
        price = order.get("price", 0.0)
        
        if not stock_code or quantity <= 0 or price <= 0:
            self.logger.error(f"订单参数无效: {order}")
            return None
        
        # 使用自定义费率或默认值
        comm = commission if commission is not None else self.commission
        slip = slippage if slippage is not None else self.slippage
        
        # 计算实际成交价（考虑滑点）
        if action == "buy":
            executed_price = price * (1 + slip)  # 买入价偏高
        else:
            executed_price = price * (1 - slip)  # 卖出价偏低
        
        # 执行订单
        if action == "buy":
            return self._execute_buy(stock_code, quantity, executed_price, portfolio, comm, order.get("reason"))
        elif action == "sell":
            return self._execute_sell(stock_code, quantity, executed_price, portfolio, comm, order.get("reason"))
        else:
            self.logger.error(f"未知订单操作: {action}")
            return None
    
    def _execute_buy(self, 
                      stock_code: str, 
                      quantity: int, 
                      price: float, 
                      portfolio: Any, 
                      commission: float,
                      reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        执行买入订单
        
        Args:
            stock_code: 股票代码
            quantity: 买入数量
            price: 买入价格
            portfolio: 投资组合对象
            commission: 佣金费率
            reason: 交易原因（可选）
            
        Returns:
            Dict: 交易记录（None 表示执行失败）
        """
        # 计算总成本
        amount = quantity * price
        comm_fee = amount * commission
        total_cost = amount + comm_fee
        
        # 检查资金是否充足
        if portfolio.cash < total_cost:
            self.logger.warning(f"资金不足: 需要 {total_cost:.2f}, 可用 {portfolio.cash:.2f}")
            return None
        
        # 执行买入
        portfolio.cash -= total_cost
        
        # 更新持仓
        if stock_code in portfolio.positions:
            # 已有持仓，计算新的平均成本
            old_quantity = portfolio.positions[stock_code]
            old_cost = portfolio.cost_basis.get(stock_code, 0.0)
            
            new_quantity = old_quantity + quantity
            new_cost = (old_cost * old_quantity + amount) / new_quantity
            
            portfolio.positions[stock_code] = new_quantity
            portfolio.cost_basis[stock_code] = new_cost
        else:
            # 新持仓
            portfolio.positions[stock_code] = quantity
            portfolio.cost_basis[stock_code] = price
        
        # 记录交易
        trade = {
            "stock_code": stock_code,
            "action": "buy",
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "commission": comm_fee,
            "slippage": amount * (self.slippage if hasattr(self, 'slippage') else 0.001),
            "reason": reason,
            "timestamp": portfolio.current_date
        }
        
        portfolio.trades.append(trade)
        
        self.logger.info(f"✓ 买入执行: {stock_code} {quantity}股 @ {price:.2f} (总成本: {total_cost:.2f})")
        return trade
    
    def _execute_sell(self, 
                       stock_code: str, 
                       quantity: int, 
                       price: float, 
                       portfolio: Any, 
                       commission: float,
                       reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        执行卖出订单
        
        Args:
            stock_code: 股票代码
            quantity: 卖出数量
            price: 卖出价格
            portfolio: 投资组合对象
            commission: 佣金费率
            reason: 交易原因（可选）
            
        Returns:
            Dict: 交易记录（None 表示执行失败）
        """
        # 检查持仓是否充足
        if stock_code not in portfolio.positions or portfolio.positions[stock_code] < quantity:
            available = portfolio.positions.get(stock_code, 0)
            self.logger.warning(f"持仓不足: {stock_code} 持有 {available}股, 尝试卖出 {quantity}股")
            return None
        
        # 计算总收入
        amount = quantity * price
        comm_fee = amount * commission
        net_income = amount - comm_fee
        
        # 计算盈亏
        cost_basis = portfolio.cost_basis.get(stock_code, price)
        profit = (price - cost_basis) * quantity - comm_fee
        
        # 执行卖出
        portfolio.cash += net_income
        
        # 更新持仓
        portfolio.positions[stock_code] -= quantity
        if portfolio.positions[stock_code] == 0:
            del portfolio.positions[stock_code]
            del portfolio.cost_basis[stock_code]
        
        # 记录交易
        trade = {
            "stock_code": stock_code,
            "action": "sell",
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "commission": comm_fee,
            "slippage": amount * (self.slippage if hasattr(self, 'slippage') else 0.001),
            "profit": profit,
            "reason": reason,
            "timestamp": portfolio.current_date
        }
        
        portfolio.trades.append(trade)
        
        self.logger.info(f"✓ 卖出执行: {stock_code} {quantity}股 @ {price:.2f} (盈亏: {profit:.2f})")
        return trade
    
    def calculate_slippage(self, 
                          order: Dict[str, Any], 
                          market_data: Optional[pd.DataFrame] = None) -> float:
        """
        计算滑点（可根据市场数据动态调整）
        
        Args:
            order: 订单信息
            market_data: 市场数据（可选）
            
        Returns:
            float: 滑点（占价格的比例）
        """
        # 基础滑点
        base_slippage = self.slippage
        
        # TODO: 根据市场数据调整滑点
        # 例如：成交量大的股票滑点小，成交量小的股票滑点大
        
        return base_slippage
    
    def set_commission(self, commission: float) -> None:
        """
        设置佣金费率
        
        Args:
            commission: 佣金费率（如 0.0003 = 万3）
        """
        if 0 <= commission <= 0.01:  # 0-1%
            self.commission = commission
            self.logger.info(f"佣金费率设置为: {commission:.4f}")
        else:
            self.logger.error(f"无效的佣金费率: {commission}")
    
    def set_slippage(self, slippage: float) -> None:
        """
        设置滑点
        
        Args:
            slippage: 滑点（如 0.001 = 0.1%）
        """
        if 0 <= slippage <= 0.05:  # 0-5%
            self.slippage = slippage
            self.logger.info(f"滑点设置为: {slippage:.4f}")
        else:
            self.logger.error(f"无效的滑点: {slippage}")
