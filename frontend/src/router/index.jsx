import React from 'react'
import Landing from '../pages/Landing'
import Login from '../pages/Login'
import Signup from '../pages/Signup'
import Setup from '../pages/Setup'
import Dashboard from '../pages/Dashboard'
import CheckinConfirm from '../pages/CheckinConfirm'

const routes = [
  { path: '/', element: <Landing /> },
  { path: '/login', element: <Login /> },
  { path: '/signup', element: <Signup /> },
  { path: '/setup', element: <Setup /> },
  { path: '/dashboard', element: <Dashboard /> },
  { path: '/checkin/confirm', element: <CheckinConfirm /> },
]

export default routes
