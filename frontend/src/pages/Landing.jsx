import React from 'react'
import { Link } from 'react-router-dom'
import Nav from '../components/Nav'

export default function Landing(){
  return (
    <div>
      <Nav />
      <main className="container-max py-20">
        <section className="grid gap-8">
          <div className="max-w-xl">
            <h1 className="text-3xl font-semibold text-sky-700">Daily check-ins for peace of mind.</h1>
            <p className="mt-4 text-gray-600">Simple, gentle check-ins that help keep you and your loved ones safe. This is a minimal frontend to test backend flows.</p>
            <div className="mt-6 flex gap-3">
              <Link to="/signup" className="px-4 py-2 bg-sky-500 text-white rounded">Get started</Link>
              <Link to="/login" className="px-4 py-2 border border-gray-200 rounded text-gray-700">Log in</Link>
            </div>
          </div>
          <div>
            <div className="card p-6 rounded shadow-sm">
              <h3 className="font-medium">How it works</h3>
              <ol className="mt-3 text-sm text-gray-600 list-decimal pl-5 space-y-2">
                <li>Set up check-in schedule and an emergency contact.</li>
                <li>Receive gentle check-ins by email.</li>
                <li>If you don’t respond, your contact is notified.</li>
              </ol>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
