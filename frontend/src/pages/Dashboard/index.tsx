import React from 'react'
import { Box, Typography, Paper, Grid, Card, CardContent } from '@mui/material'
import { useAppSelector } from '@/store/hooks'
import { useEffect } from 'react'
import { fetchStrategyList } from '@/store/strategySlice'
import { useAppDispatch } from '@/store/hooks'
import { fetchStockList } from '@/store/stockSlice'

const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch()
  const { list: strategies } = useAppSelector((state) => state.strategy)
  const { total } = useAppSelector((state) => state.stock)

  useEffect(() => {
    dispatch(fetchStrategyList())
    dispatch(fetchStockList({ page: 1, page_size: 10 }))
  }, [dispatch])

  const stats = [
    { label: '股票数量', value: total || 0 },
    { label: '策略数量', value: strategies.length || 0 },
    { label: '回测次数', value: 0 },
    { label: '系统状态', value: '正常' },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        系统概览
      </Typography>
      <Grid container spacing={3} mb={3}>
        {stats.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.label}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {stat.label}
                </Typography>
                <Typography variant="h5">{stat.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          快速开始
        </Typography>
        <Typography paragraph>
          欢迎使用 A股量化交易选股系统！您可以通过侧边栏导航到不同功能模块。
        </Typography>
        <Typography>
          • 查看<strong>股票列表</strong>浏览可交易的 A 股股票
        </Typography>
        <Typography>
          • 在<strong>策略管理</strong>中创建和配置交易策略
        </Typography>
        <Typography>
          • 使用<strong>运行回测</strong>测试策略在历史数据上的表现
        </Typography>
      </Paper>
    </Box>
  )
}

export default Dashboard
