import apiClient from './client'

export interface StockInfo {
  code: string
  name: string
  industry?: string
  list_date?: string
}

export interface StockDaily {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

export const stockApi = {
  getStockList: async (page = 1, pageSize = 20, keyword?: string) => {
    const params = { page, page_size: pageSize, keyword }
    return await apiClient.get('/stocks', { params })
  },

  getStockDaily: async (code: string, start: string, end: string) => {
    const params = { start_date: start, end_date: end }
    return await apiClient.get(`/stocks/${code}/daily`, { params })
  },

  searchStocks: async (keyword: string) => {
    return await apiClient.get('/stocks/search', {
      params: { q: keyword },
    })
  },
}
