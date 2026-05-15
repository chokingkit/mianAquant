import React, { useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useParams } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { fetchBacktestResults } from '@/store/backtestSlice'

const BacktestResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const dispatch = useAppDispatch()
  const { currentResult } = useAppSelector((state) => state.backtest)

  useEffect(() => {
    if (id) {
      dispatch(fetchBacktestResults(Number(id)))
    }
  }, [dispatch, id])

  if (!currentResult) {
    return <Typography>加载中...</Typography>
  }

  const metrics = [
    { label: '总收益率', value: `${(currentResult.total_return * 100).toFixed(2)}%` },
    { label: '年化收益率', value: `${(currentResult.annual_return * 100).toFixed(2)}%` },
    { label: '夏普比率', value: currentResult.sharpe_ratio.toFixed(2) },
    { label: '最大回撤', value: `${(currentResult.max_drawdown * 100).toFixed(2)}%` },
    { label: '胜率', value: `${(currentResult.win_rate * 100).toFixed(2)}%` },
    { label: '总交易次数', value: currentResult.total_trades },
  ]

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        回测结果
      </Typography>

      {/* 指标卡片 */}
      <Grid container spacing={3} mb={3}>
        {metrics.map((metric) => (
          <Grid item xs={12} sm={6} md={4} key={metric.label}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {metric.label}
                </Typography>
                <Typography variant="h5">{metric.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 权益曲线 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          权益曲线
        </Typography>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={currentResult.equity_curve}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="equity"
              stroke="#1976d2"
              name="权益"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </Paper>

      {/* 交易记录 */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          交易记录
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>日期</TableCell>
                <TableCell>股票</TableCell>
                <TableCell>操作</TableCell>
                <TableCell align="right">价格</TableCell>
                <TableCell align="right">数量</TableCell>
                <TableCell align="right">盈亏</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {currentResult.trades.map((trade: any, index: number) => (
                <TableRow key={index}>
                  <TableCell>{trade.date}</TableCell>
                  <TableCell>{trade.symbol}</TableCell>
                  <TableCell>
                    <span style={{ color: trade.side === 'buy' ? '#4caf50' : '#f44336' }}>
                      {trade.side === 'buy' ? '买入' : '卖出'}
                    </span>
                  </TableCell>
                  <TableCell align="right">{trade.price.toFixed(2)}</TableCell>
                  <TableCell align="right">{trade.quantity}</TableCell>
                  <TableCell align="right">
                    {trade.pnl !== undefined && (
                      <span style={{ color: trade.pnl >= 0 ? '#4caf50' : '#f44336' }}>
                        {trade.pnl.toFixed(2)}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  )
}

export default BacktestResultsPage
