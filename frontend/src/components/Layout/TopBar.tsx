import React from 'react'
import { AppBar, Toolbar, Typography, Box } from '@mui/material'

const TopBar: React.FC = () => {
  return (
    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          A股量化交易选股系统
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
      </Toolbar>
    </AppBar>
  )
}

export default TopBar
