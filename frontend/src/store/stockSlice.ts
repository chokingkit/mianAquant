import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { StockInfo, StockDaily } from '@/types'
import { stockApi } from '@/api/stockApi'

interface StockState {
  list: StockInfo[]
  total: number
  currentStock: StockInfo | null
  dailyData: StockDaily[]
  loading: boolean
  error: string | null
}

const initialState: StockState = {
  list: [],
  total: 0,
  currentStock: null,
  dailyData: [],
  loading: false,
  error: null,
}

export const fetchStockList = createAsyncThunk(
  'stock/fetchList',
  async (params: { page: number; page_size: number; keyword?: string }) => {
    const response = await stockApi.getStockList(params.page, params.page_size, params.keyword)
    return response.data  // 提取 response.data
  }
)

export const fetchStockDaily = createAsyncThunk(
  'stock/fetchDaily',
  async (params: { code: string; start: string; end: string }) => {
    const response = await stockApi.getStockDaily(params.code, params.start, params.end)
    return response.data  // 提取 response.data
  }
)

const stockSlice = createSlice({
  name: 'stock',
  initialState,
  reducers: {
    setCurrentStock: (state, action) => {
      state.currentStock = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStockList.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchStockList.fulfilled, (state, action) => {
        state.loading = false
        // response.data = { total: number, data: StockInfo[] }
        const payload = action.payload as { total: number; data: StockInfo[] }
        state.list = payload.data || payload
        state.total = payload.total || (payload.data ? payload.data.length : 0)
      })
      .addCase(fetchStockList.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取股票列表失败'
      })
      .addCase(fetchStockDaily.fulfilled, (state, action) => {
        state.dailyData = action.payload as StockDaily[]
      })
  },
})

export const { setCurrentStock, clearError } = stockSlice.actions
export default stockSlice.reducer
