import React, { useEffect, useState } from 'react'
import {
  DataGrid,
  GridColDef,
  GridPaginationModel,
} from '@mui/x-data-grid'
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Search as SearchIcon } from '@mui/icons-material'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { fetchStockList, setCurrentStock } from '@/store/stockSlice'
import { useNavigate } from 'react-router-dom'

const StockListPage: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { list, total, loading } = useAppSelector((state) => state.stock)
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  })
  const [keyword, setKeyword] = useState('')

  useEffect(() => {
    dispatch(fetchStockList({
      page: paginationModel.page + 1,
      page_size: paginationModel.pageSize,
      keyword,
    }))
  }, [dispatch, paginationModel, keyword])

  const columns: GridColDef[] = [
    { field: 'code', headerName: '股票代码', width: 120 },
    { field: 'name', headerName: '股票名称', width: 150 },
    { field: 'industry', headerName: '行业', width: 150 },
    { field: 'list_date', headerName: '上市日期', width: 120 },
    {
      field: 'actions',
      headerName: '操作',
      width: 150,
      renderCell: (params) => (
        <Button
          variant="contained"
          size="small"
          onClick={() => {
            dispatch(setCurrentStock(params.row))
            navigate(`/stocks/${params.row.code}`)
          }}
        >
          查看详情
        </Button>
      ),
    },
  ]

  const handleSearch = () => {
    setPaginationModel(prev => ({ ...prev, page: 0 }))
    dispatch(fetchStockList({ page: 1, page_size: paginationModel.pageSize, keyword }))
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        股票列表
      </Typography>
      <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
        <TextField
          label="搜索股票（代码/名称）"
          variant="outlined"
          size="small"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyUp={(e) => {
            if (e.key === 'Enter') {
              handleSearch()
            }
          }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={handleSearch} size="small">
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mr: 2, minWidth: 300 }}
        />
      </Paper>
      <Paper elevation={3} sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={list}
          columns={columns}
          paginationModel={paginationModel}
          rowCount={total}
          loading={loading}
          paginationMode="server"
          onPaginationModelChange={(model) => setPaginationModel(model)}
          getRowId={(row) => row.code}
          disableRowSelectionOnClick
        />
      </Paper>
    </Box>
  )
}

export default StockListPage
