"""
风险规则模块
定义基础风险规则类和具体规则实现
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class BaseRiskRule:
    """
    风险规则基类
    
    所有风险规则必须继承此类并实现 check 方法
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any], rule_id: Optional[int] = None):
        """
        初始化风险规则
        
        Args:
            name: 规则名称
            parameters: 规则参数
            rule_id: 规则 ID（数据库中的 ID）
        """
        self.name = name
        self.parameters = parameters
        self.rule_id = rule_id
        self.enabled = True
        self.priority = 100
    
    def check(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查风险规则是否触发
        
        Args:
            context: 风险检查上下文，包含：
                - portfolio: 当前持仓信息
                - positions: 持仓明细
                - market_data: 市场数据
                - trades: 交易记录
                
        Returns:
            Optional[Dict]: 如果规则触发，返回告警信息；否则返回 None
        """
        raise NotImplementedError("子类必须实现 check 方法")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.rule_id,
            'name': self.name,
            'parameters': self.parameters,
            'enabled': self.enabled,
            'priority': self.priority,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseRiskRule':
        """从字典创建规则实例"""
        raise NotImplementedError("子类必须实现 from_dict 方法")


class PositionLimitRule(BaseRiskRule):
    """
    仓位限制规则
    
    限制单个股票的持仓比例或持仓数量
    
    参数示例：
        {
            "max_position_value": 100000,  # 最大持仓金额
            "max_position_ratio": 0.1,     # 最大持仓比例（占总资产）
            "max_position_count": 10,       # 最大持仓数量（只）
            "stock_code": "sh.600000"       # 可选，限制特定股票
        }
    """
    
    def check(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查仓位限制
        
        Args:
            context: 包含 portfolio 和 positions
            
        Returns:
            Optional[Dict]: 触发时返回告警信息
        """
        portfolio = context.get('portfolio', {})
        positions = context.get('positions', {})
        
        total_value = portfolio.get('total_value', 0)
        max_ratio = self.parameters.get('max_position_ratio')
        max_value = self.parameters.get('max_position_value')
        max_count = self.parameters.get('max_position_count')
        target_stock = self.parameters.get('stock_code')
        
        alerts = []
        
        # 检查持仓数量
        if max_count is not None and len(positions) > max_count:
            alerts.append({
                'rule_name': self.name,
                'rule_type': 'position_limit',
                'alert_level': 'warning',
                'message': f'持仓数量超限: 当前 {len(positions)} 只，限制 {max_count} 只',
                'details': {
                    'current_count': len(positions),
                    'max_count': max_count
                }
            })
        
        # 检查单个持仓比例
        if max_ratio is not None:
            for stock_code, position in positions.items():
                if target_stock and stock_code != target_stock:
                    continue
                
                position_value = position.get('value', 0)
                ratio = position_value / total_value if total_value > 0 else 0
                
                if ratio > max_ratio:
                    alerts.append({
                        'rule_name': self.name,
                        'rule_type': 'position_limit',
                        'alert_level': 'warning',
                        'message': f'持仓比例超限: {stock_code} 占比 {ratio:.2%}，限制 {max_ratio:.2%}',
                        'details': {
                            'stock_code': stock_code,
                            'position_value': position_value,
                            'total_value': total_value,
                            'current_ratio': ratio,
                            'max_ratio': max_ratio
                        }
                    })
        
        # 检查单个持仓金额
        if max_value is not None:
            for stock_code, position in positions.items():
                if target_stock and stock_code != target_stock:
                    continue
                
                position_value = position.get('value', 0)
                
                if position_value > max_value:
                    alerts.append({
                        'rule_name': self.name,
                        'rule_type': 'position_limit',
                        'alert_level': 'warning',
                        'message': f'持仓金额超限: {stock_code} 市值 {position_value:.2f}，限制 {max_value:.2f}',
                        'details': {
                            'stock_code': stock_code,
                            'position_value': position_value,
                            'max_value': max_value
                        }
                    })
        
        return alerts if alerts else None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PositionLimitRule':
        """从字典创建规则实例"""
        return cls(
            name=data.get('name', '仓位限制规则'),
            parameters=data.get('parameters', {}),
            rule_id=data.get('id')
        )


class StopLossRule(BaseRiskRule):
    """
    止损规则
    
    当亏损达到设定阈值时触发告警
    
    参数示例：
        {
            "stop_loss_ratio": 0.05,     # 止损比例（5% 亏损触发）
            "stop_loss_amount": 5000,     # 止损金额（可选）
            "trailing_stop": True,        # 是否启用追踪止损
            "trailing_stop_ratio": 0.03,  # 追踪止损比例
            "stock_code": "sh.600000"     # 可选，限制特定股票
        }
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any], rule_id: Optional[int] = None):
        super().__init__(name, parameters, rule_id)
        self.highest_price = {}  # 追踪最高价（用于追踪止损）
    
    def check(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查止损规则
        
        Args:
            context: 包含 positions, market_data
            
        Returns:
            Optional[Dict]: 触发时返回告警信息
        """
        positions = context.get('positions', {})
        market_data = context.get('market_data', {})
        
        stop_loss_ratio = self.parameters.get('stop_loss_ratio', 0.05)
        stop_loss_amount = self.parameters.get('stop_loss_amount')
        trailing_stop = self.parameters.get('trailing_stop', False)
        trailing_stop_ratio = self.parameters.get('trailing_stop_ratio', 0.03)
        target_stock = self.parameters.get('stock_code')
        
        alerts = []
        
        for stock_code, position in positions.items():
            if target_stock and stock_code != target_stock:
                continue
            
            current_price = market_data.get(stock_code, {}).get('close', 0)
            cost_price = position.get('cost_price', 0)
            quantity = position.get('quantity', 0)
            
            if current_price <= 0 or cost_price <= 0:
                continue
            
            # 更新追踪最高价
            if trailing_stop:
                if stock_code not in self.highest_price:
                    self.highest_price[stock_code] = cost_price
                self.highest_price[stock_code] = max(self.highest_price[stock_code], current_price)
            
            # 计算亏损比例
            loss_ratio = (cost_price - current_price) / cost_price
            loss_amount = (cost_price - current_price) * quantity
            
            # 检查固定止损
            if loss_ratio > stop_loss_ratio:
                alerts.append({
                    'rule_name': self.name,
                    'rule_type': 'stop_loss',
                    'alert_level': 'critical' if loss_ratio > stop_loss_ratio * 2 else 'warning',
                    'message': f'触发止损: {stock_code} 亏损 {loss_ratio:.2%}，成本 {cost_price:.2f}，现价 {current_price:.2f}',
                    'details': {
                        'stock_code': stock_code,
                        'cost_price': cost_price,
                        'current_price': current_price,
                        'loss_ratio': loss_ratio,
                        'loss_amount': loss_amount,
                        'stop_loss_ratio': stop_loss_ratio
                    }
                })
            
            # 检查止损金额
            if stop_loss_amount and loss_amount > stop_loss_amount:
                alerts.append({
                    'rule_name': self.name,
                    'rule_type': 'stop_loss',
                    'alert_level': 'critical',
                    'message': f'触发止损金额: {stock_code} 亏损 {loss_amount:.2f}，限制 {stop_loss_amount:.2f}',
                    'details': {
                        'stock_code': stock_code,
                        'loss_amount': loss_amount,
                        'stop_loss_amount': stop_loss_amount
                    }
                })
            
            # 检查追踪止损
            if trailing_stop and stock_code in self.highest_price:
                highest = self.highest_price[stock_code]
                trailing_loss_ratio = (highest - current_price) / highest
                
                if trailing_loss_ratio > trailing_stop_ratio:
                    alerts.append({
                        'rule_name': self.name,
                        'rule_type': 'stop_loss',
                        'alert_level': 'warning',
                        'message': f'触发追踪止损: {stock_code} 从最高价 {highest:.2f} 回落 {trailing_loss_ratio:.2%}',
                        'details': {
                            'stock_code': stock_code,
                            'highest_price': highest,
                            'current_price': current_price,
                            'trailing_loss_ratio': trailing_loss_ratio,
                            'trailing_stop_ratio': trailing_stop_ratio
                        }
                    })
        
        return alerts if alerts else None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StopLossRule':
        """从字典创建规则实例"""
        return cls(
            name=data.get('name', '止损规则'),
            parameters=data.get('parameters', {}),
            rule_id=data.get('id')
        )


class TakeProfitRule(BaseRiskRule):
    """
    止盈规则
    
    当盈利达到设定阈值时触发告警
    
    参数示例：
        {
            "take_profit_ratio": 0.20,    # 止盈比例（20% 盈利触发）
            "take_profit_amount": 20000,   # 止盈金额（可选）
            "trailing_profit": True,       # 是否启用追踪止盈
            "trailing_profit_ratio": 0.05, # 追踪止盈回撤比例
            "stock_code": "sh.600000"      # 可选，限制特定股票
        }
    """
    
    def __init__(self, name: str, parameters: Dict[str, Any], rule_id: Optional[int] = None):
        super().__init__(name, parameters, rule_id)
        self.highest_profit_ratio = {}  # 追踪最高盈利比例
    
    def check(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        检查止盈规则
        
        Args:
            context: 包含 positions, market_data
            
        Returns:
            Optional[Dict]: 触发时返回告警信息
        """
        positions = context.get('positions', {})
        market_data = context.get('market_data', {})
        
        take_profit_ratio = self.parameters.get('take_profit_ratio', 0.20)
        take_profit_amount = self.parameters.get('take_profit_amount')
        trailing_profit = self.parameters.get('trailing_profit', False)
        trailing_profit_ratio = self.parameters.get('trailing_profit_ratio', 0.05)
        target_stock = self.parameters.get('stock_code')
        
        alerts = []
        
        for stock_code, position in positions.items():
            if target_stock and stock_code != target_stock:
                continue
            
            current_price = market_data.get(stock_code, {}).get('close', 0)
            cost_price = position.get('cost_price', 0)
            quantity = position.get('quantity', 0)
            
            if current_price <= 0 or cost_price <= 0:
                continue
            
            # 计算盈利比例
            profit_ratio = (current_price - cost_price) / cost_price
            profit_amount = (current_price - cost_price) * quantity
            
            # 更新追踪最高盈利
            if trailing_profit:
                current_ratio = profit_ratio
                if stock_code not in self.highest_profit_ratio:
                    self.highest_profit_ratio[stock_code] = current_ratio
                self.highest_profit_ratio[stock_code] = max(
                    self.highest_profit_ratio[stock_code], current_ratio
                )
            
            # 检查固定止盈
            if profit_ratio > take_profit_ratio:
                alerts.append({
                    'rule_name': self.name,
                    'rule_type': 'take_profit',
                    'alert_level': 'info',
                    'message': f'触发止盈: {stock_code} 盈利 {profit_ratio:.2%}，成本 {cost_price:.2f}，现价 {current_price:.2f}',
                    'details': {
                        'stock_code': stock_code,
                        'cost_price': cost_price,
                        'current_price': current_price,
                        'profit_ratio': profit_ratio,
                        'profit_amount': profit_amount,
                        'take_profit_ratio': take_profit_ratio
                    }
                })
            
            # 检查止盈金额
            if take_profit_amount and profit_amount > take_profit_amount:
                alerts.append({
                    'rule_name': self.name,
                    'rule_type': 'take_profit',
                    'alert_level': 'info',
                    'message': f'触发止盈金额: {stock_code} 盈利 {profit_amount:.2f}，目标 {take_profit_amount:.2f}',
                    'details': {
                        'stock_code': stock_code,
                        'profit_amount': profit_amount,
                        'take_profit_amount': take_profit_amount
                    }
                })
            
            # 检查追踪止盈
            if trailing_profit and stock_code in self.highest_profit_ratio:
                highest_ratio = self.highest_profit_ratio[stock_code]
                current_ratio = profit_ratio
                drawdown = highest_ratio - current_ratio
                
                if drawdown > trailing_profit_ratio and current_ratio > 0:
                    alerts.append({
                        'rule_name': self.name,
                        'rule_type': 'take_profit',
                        'alert_level': 'info',
                        'message': f'触发追踪止盈: {stock_code} 从最高盈利 {highest_ratio:.2%} 回撤 {drawdown:.2%}',
                        'details': {
                            'stock_code': stock_code,
                            'highest_profit_ratio': highest_ratio,
                            'current_profit_ratio': current_ratio,
                            'drawdown': drawdown,
                            'trailing_profit_ratio': trailing_profit_ratio
                        }
                    })
        
        return alerts if alerts else None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TakeProfitRule':
        """从字典创建规则实例"""
        return cls(
            name=data.get('name', '止盈规则'),
            parameters=data.get('parameters', {}),
            rule_id=data.get('id')
        )


# 规则类型映射
RULE_TYPE_MAP = {
    'position_limit': PositionLimitRule,
    'stop_loss': StopLossRule,
    'take_profit': TakeProfitRule,
}


def create_rule(rule_type: str, name: str, parameters: Dict[str, Any], rule_id: Optional[int] = None) -> BaseRiskRule:
    """
    工厂函数：根据规则类型创建规则实例
    
    Args:
        rule_type: 规则类型
        name: 规则名称
        parameters: 规则参数
        rule_id: 规则 ID
        
    Returns:
        BaseRiskRule: 规则实例
        
    Raises:
        ValueError: 未知的规则类型
    """
    rule_class = RULE_TYPE_MAP.get(rule_type)
    if not rule_class:
        raise ValueError(f"未知的规则类型: {rule_type}")
    
    return rule_class(name=name, parameters=parameters, rule_id=rule_id)


def get_rule_types() -> List[str]:
    """
    获取所有支持的规则类型
    
    Returns:
        List[str]: 规则类型列表
    """
    return list(RULE_TYPE_MAP.keys())
