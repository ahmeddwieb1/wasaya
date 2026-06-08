import React, {useEffect, useState} from 'react'
import Nav from '../components/Nav'
import axios from '../api/axios'
import { useNavigate } from 'react-router-dom'

export default function Dashboard(){
  const [status, setStatus] = useState('Unknown')
  const [last, setLast] = useState(null)
  const [next, setNext] = useState(null)
  const [contact, setContact] = useState(null)
  const [message, setMessage] = useState(null)
  const navigate = useNavigate()

  async function load(){
    try{
      const res = await axios.get('/api/v1/dashboard')
      const data = res.data || {}
      setStatus(data.status || 'Active')
      setLast(data.last_checkin || null)
      setNext(data.next_checkin || null)
      setContact(data.emergency_contact || null)
    }catch(err){
      setMessage('Could not load dashboard')
    }
  }

  useEffect(()=>{load()}, [])

  async function checkinNow(){
    setMessage(null)
    try{
      await axios.post('/api/v1/checkin')
      navigate('/checkin/confirm')
    }catch(err){
      setMessage('Check-in failed')
    }
  }

  async function pause(){
    try{
      await axios.post('/api/v1/settings/pause')
      setMessage('Check-ins paused')
    }catch(err){
      setMessage('Failed to pause')
    }
  }

  return (
    <div>
      <Nav />
      <main className="container-max py-12">
        <div className="card p-6 rounded shadow max-w-lg mx-auto">
          <h2 className="text-lg font-semibold">Dashboard</h2>
          {message && <div className="text-sm text-sky-700 my-3">{message}</div>}
          <div className="mt-4 space-y-3 text-sm text-gray-700">
            <div><span className="font-medium">Status:</span> {status}</div>
            <div><span className="font-medium">Last check-in:</span> {last || '—'}</div>
            <div><span className="font-medium">Next check-in:</span> {next || '—'}</div>
            <div><span className="font-medium">Emergency contact:</span> {contact ? `${contact.name} — ${contact.email}` : '—'}</div>
          </div>

          <div className="mt-6 flex gap-3">
            <button onClick={()=>navigate('/setup')} className="px-3 py-2 bg-white border border-gray-200 rounded">Update settings</button>
            <button onClick={pause} className="px-3 py-2 bg-white border border-gray-200 rounded">Pause check-ins</button>
            <button onClick={checkinNow} className="px-3 py-2 bg-sky-500 text-white rounded">Check in now</button>
          </div>
        </div>
      </main>
    </div>
  )
}
