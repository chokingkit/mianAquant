import apiClient from './client'

export interface BacktestRequest {
  strategy_id: number
  start_date: string
  end_date: string
  initial_cash: number
}

export interface BacktestResult {
  id: number
  strategy_id: number
  total_return: number
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
  equity_curve: Array<{ date: string; equity: number }>
  trades: Array<{
    date: string
    symbol: string
    side: 'buy' | 'sell'
    price: number
    quantity: number
    pnl?: number
  }>
}

export const backtestApi = {
  runBacktest: async (request: BacktestRequest) => {
    return await apiClient.post('/backtest/run', request)
  },

  getBacktestResults: async (id: number) => {
    return await apiClient.get(`/backtest/${id}/results`)
  },

  getBacktestList: async () => {
    return await apiClient.get('/backtest/list')
  },

  generateReport: async (id: number) => {
    return await apiClient.get(`/backtest/${id}/report`)
  },
}
