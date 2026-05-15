export interface StrategyConfig {
  id?: number
  name: string
  strategy_type: 'MAStrategy' | 'MACDStrategy' | 'RSIStrategy'
  parameters: {
    short_window?: number
    long_window?: number
    fast_period?: number
    slow_period?: number
    signal_period?: number
    oversold?: number
    overbought?: number
  }
  stock_pool: string[]
  description?: string
}

export interface StrategyDefaultParams {
  [key: string]: {
    [param: string]: number
  }
}
