import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { StrategyConfig } from '@/types'
import { strategyApi } from '@/api/strategyApi'

interface StrategyState {
  list: StrategyConfig[]
  currentStrategy: StrategyConfig | null
  loading: boolean
  error: string | null
}

const initialState: StrategyState = {
  list: [],
  currentStrategy: null,
  loading: false,
  error: null,
}

export const fetchStrategyList = createAsyncThunk(
  'strategy/fetchList',
  async () => {
    const response = await strategyApi.getStrategyList()
    return response.data
  }
)

export const createNewStrategy = createAsyncThunk(
  'strategy/create',
  async (config: StrategyConfig) => {
    const response = await strategyApi.createStrategy(config)
    return response.data
  }
)

const strategySlice = createSlice({
  name: 'strategy',
  initialState,
  reducers: {
    setCurrentStrategy: (state, action) => {
      state.currentStrategy = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStrategyList.fulfilled, (state, action) => {
        state.list = action.payload as StrategyConfig[]
      })
      .addCase(createNewStrategy.fulfilled, (state, action) => {
        state.list.push(action.payload as StrategyConfig)
      })
  },
})

export const { setCurrentStrategy, clearError: clearStrategyError } = strategySlice.actions
export default strategySlice.reducer
