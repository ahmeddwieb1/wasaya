import React from 'react'
import { Link } from 'react-router-dom'

export default function Nav(){
  return (
    <nav className="w-full py-4 bg-transparent">
      <div className="container-max flex items-center justify-between">
        <Link to="/" className="text-lg font-semibold text-sky-600">Wasaya</Link>
        <div className="space-x-3">
          <Link to="/login" className="text-sm text-slate-700">Log in</Link>
          <Link to="/signup" className="text-sm text-white bg-sky-500 px-3 py-1 rounded">Sign up</Link>
        </div>
      </div>
    </nav>
  )
}
