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

export interface StockSearchResult {
  code: string
  name: string
  match_reason?: string
}
