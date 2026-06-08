import React from 'react'
import Nav from '../components/Nav'

export default function CheckinConfirm(){
  return (
    <div>
      <Nav />
      <main className="container-max py-20">
        <div className="max-w-md mx-auto card p-8 rounded shadow text-center">
          <h2 className="text-xl font-semibold text-sky-700">You're marked safe</h2>
          <p className="mt-3 text-gray-600">Thank you — your check-in was recorded.</p>
        </div>
      </main>
    </div>
  )
}
