import React from 'react'
import { Box, Typography, Paper } from '@mui/material'
import { useAppSelector } from '@/store/hooks'
import { useParams } from 'react-router-dom'

const StockDetailPage: React.FC = () => {
  const { code } = useParams<{ code: string }>()
  const { currentStock, dailyData } = useAppSelector((state) => state.stock)

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        股票详情: {currentStock?.name || code}
      </Typography>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          基本信息
        </Typography>
        <Typography>代码: {currentStock?.code}</Typography>
        <Typography>名称: {currentStock?.name}</Typography>
        <Typography>行业: {currentStock?.industry || '未知'}</Typography>
        <Typography>上市日期: {currentStock?.list_date || '未知'}</Typography>
      </Paper>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          日线数据 ({dailyData.length} 条记录)
        </Typography>
        {dailyData.length > 0 ? (
          <pre>{JSON.stringify(dailyData.slice(0, 5), null, 2)}</pre>
        ) : (
          <Typography>暂无数据</Typography>
        )}
      </Paper>
    </Box>
  )
}

export default StockDetailPage
