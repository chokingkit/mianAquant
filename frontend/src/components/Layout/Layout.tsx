import React from 'react'
import { Box, Container } from '@mui/material'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { Outlet } from 'react-router-dom'

const Layout: React.FC = () => {
  return (
    <Box sx={{ display: 'flex' }}>
      <TopBar />
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          marginLeft: '240px',
          marginTop: '64px',
          width: 'calc(100% - 240px)',
        }}
      >
        <Container maxWidth="xl">
          <Outlet />
        </Container>
      </Box>
    </Box>
  )
}

export default Layout
