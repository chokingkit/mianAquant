import apiClient from './client'

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

export const strategyApi = {
  createStrategy: async (config: StrategyConfig) => {
    return await apiClient.post('/strategies', config)
  },

  getStrategyList: async () => {
    return await apiClient.get('/strategies')
  },

  getStrategy: async (id: number) => {
    return await apiClient.get(`/strategies/${id}`)
  },

  updateStrategy: async (id: number, config: Partial<StrategyConfig>) => {
    return await apiClient.put(`/strategies/${id}`, config)
  },

  deleteStrategy: async (id: number) => {
    return await apiClient.delete(`/strategies/${id}`)
  },
}
