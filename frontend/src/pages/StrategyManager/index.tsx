import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
} from '@mui/material'
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { fetchStrategyList, createNewStrategy } from '@/store/strategySlice'
import { StrategyConfig } from '@/types'

const StrategyManagerPage: React.FC = () => {
  const dispatch = useAppDispatch()
  const { list, loading } = useAppSelector((state) => state.strategy)
  const [open, setOpen] = useState(false)
  const [formData, setFormData] = useState<Partial<StrategyConfig>>({
    name: '',
    strategy_type: 'MAStrategy',
    parameters: { short_window: 5, long_window: 20 },
    stock_pool: [],
    description: '',
  })

  useEffect(() => {
    dispatch(fetchStrategyList())
  }, [dispatch])

  const handleCreate = async () => {
    try {
      const params: StrategyConfig = {
        name: formData.name || '',
        strategy_type: formData.strategy_type || 'MAStrategy',
        parameters: formData.parameters || {},
        stock_pool: formData.stock_pool || [],
        description: formData.description || '',
      }
      await dispatch(createNewStrategy(params))
      setOpen(false)
      setFormData({
        name: '',
        strategy_type: 'MAStrategy',
        parameters: { short_window: 5, long_window: 20 },
        stock_pool: [],
        description: '',
      })
    } catch (err) {
      console.error('Failed to create strategy:', err)
    }
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        策略管理
      </Typography>
      <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
        >
          创建策略
        </Button>
      </Paper>
      <Paper elevation={3} sx={{ p: 2 }}>
        {loading ? (
          <Typography>加载中...</Typography>
        ) : (
          <List>
            {list.map((strategy) => (
              <ListItem key={strategy.id}>
                <ListItemText
                  primary={strategy.name}
                  secondary={`类型: ${strategy.strategy_type} | 股票池: ${strategy.stock_pool?.join(', ')}`}
                />
                <ListItemSecondaryAction>
                  <IconButton edge="end" aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* 创建策略对话框 */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>创建策略</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="策略名称"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>策略类型</InputLabel>
                <Select
                  value={formData.strategy_type || 'MAStrategy'}
                  label="策略类型"
                  onChange={(e) =>
                    setFormData({ ...formData, strategy_type: e.target.value as StrategyConfig['strategy_type'] })
                  }
                >
                  <MenuItem value="MAStrategy">均线交叉策略</MenuItem>
                  <MenuItem value="MACDStrategy">MACD信号策略</MenuItem>
                  <MenuItem value="RSIStrategy">RSI策略</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="参数 (JSON)"
                multiline
                rows={3}
                value={JSON.stringify(formData.parameters, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    setFormData({ ...formData, parameters: parsed })
                  } catch {
                    // ignore invalid JSON while typing
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="股票池 (逗号分隔)"
                value={(formData.stock_pool || []).join(',')}
                onChange={(e) =>
                  setFormData({ ...formData, stock_pool: e.target.value.split(',').map((s) => s.trim()) })
                }
                placeholder="sh.600000, sz.000001"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="描述"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreate} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default StrategyManagerPage
