import { configureStore } from '@reduxjs/toolkit'
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux'
import stockReducer from './stockSlice'
import strategyReducer from './strategySlice'
import backtestReducer from './backtestSlice'

export const store = configureStore({
  reducer: {
    stock: stockReducer,
    strategy: strategyReducer,
    backtest: backtestReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export const useAppDispatch: () => AppDispatch = useDispatch
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
