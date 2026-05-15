import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { store } from './store'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import StockList from './pages/StockList'
import StrategyManager from './pages/StrategyManager'
import BacktestRunner from './pages/BacktestRunner'
import BacktestResults from './pages/BacktestResults'

function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stocks" element={<StockList />} />
            <Route path="/strategies" element={<StrategyManager />} />
            <Route path="/backtest/run" element={<BacktestRunner />} />
            <Route path="/backtest/:id/results" element={<BacktestResults />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Provider>
  )
}

export default App
