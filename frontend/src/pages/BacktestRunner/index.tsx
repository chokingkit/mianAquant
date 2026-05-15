import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { runBacktest } from '@/store/backtestSlice'
import { fetchStrategyList } from '@/store/strategySlice'
import { useNavigate } from 'react-router-dom'

const BacktestRunnerPage: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { list } = useAppSelector((state) => state.strategy)
  const { loading, error } = useAppSelector((state) => state.backtest)
  const [formData, setFormData] = useState({
    strategy_id: '',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    initial_cash: 100000,
  })

  useEffect(() => {
    dispatch(fetchStrategyList())
  }, [dispatch])

  const handleSubmit = async () => {
    if (!formData.strategy_id) {
      alert('请选择策略')
      return
    }

    try {
      const result = await dispatch(
        runBacktest({
          strategy_id: Number(formData.strategy_id),
          start_date: formData.start_date,
          end_date: formData.end_date,
          initial_cash: formData.initial_cash,
        })
      ).unwrap()

      navigate(`/backtest/${result.id}/results`)
    } catch (err) {
      console.error('Backtest failed:', err)
    }
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        运行回测
      </Typography>
      <Paper elevation={3} sx={{ p: 3, maxWidth: 600 }}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>选择策略</InputLabel>
              <Select
                value={formData.strategy_id}
                label="选择策略"
                onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
              >
                {list.map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.name} ({s.strategy_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="开始日期"
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              label="结束日期"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="初始资金"
              type="number"
              value={formData.initial_cash}
              onChange={(e) => setFormData({ ...formData, initial_cash: Number(e.target.value) })}
            />
          </Grid>
          {error && (
            <Grid item xs={12}>
              <Alert severity="error">{error}</Alert>
            </Grid>
          )}
          <Grid item xs={12}>
            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : '启动回测'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  )
}

export default BacktestRunnerPage
