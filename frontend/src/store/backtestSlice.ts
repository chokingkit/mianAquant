import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { BacktestRequest, BacktestResult } from '@/types'
import { backtestApi } from '@/api/backtestApi'

interface BacktestState {
  list: BacktestResult[]
  currentResult: BacktestResult | null
  loading: boolean
  error: string | null
}

const initialState: BacktestState = {
  list: [],
  currentResult: null,
  loading: false,
  error: null,
}

export const runBacktest = createAsyncThunk(
  'backtest/run',
  async (request: BacktestRequest) => {
    const response = await backtestApi.runBacktest(request)
    return response.data
  }
)

export const fetchBacktestResults = createAsyncThunk(
  'backtest/fetchResults',
  async (id: number) => {
    const response = await backtestApi.getBacktestResults(id)
    return response.data
  }
)

const backtestSlice = createSlice({
  name: 'backtest',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(runBacktest.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(runBacktest.fulfilled, (state, action) => {
        state.loading = false
        state.currentResult = action.payload as BacktestResult
        state.list.push(action.payload as BacktestResult)
      })
      .addCase(runBacktest.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '回测失败'
      })
      .addCase(fetchBacktestResults.fulfilled, (state, action) => {
        state.currentResult = action.payload as BacktestResult
      })
  },
})

export const { clearError: clearBacktestError } = backtestSlice.actions
export default backtestSlice.reducer
