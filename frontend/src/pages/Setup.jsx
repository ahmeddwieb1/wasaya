import React, {useState, useEffect} from 'react'
import axios from '../api/axios'
import Nav from '../components/Nav'
import FormInput from '../components/FormInput'

export default function Setup(){
  const [interval, setInterval] = useState('daily')
  const [grace, setGrace] = useState(24)
  const [time, setTime] = useState('09:00')
  const [contactName, setContactName] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [message, setMessage] = useState(null)

  useEffect(()=>{
    // try to load existing settings and contacts (best-effort)
    let mounted = true
    ;(async ()=>{
      try{
        const s = await axios.get('/api/v1/settings')
        if(!mounted) return
        const data = s.data || {}
        // backend uses hours fields; map to our UI
        const intervalHours = data.check_interval_hours
        if(intervalHours === 24) setInterval('daily')
        else if(intervalHours === 168) setInterval('weekly')
        else if(intervalHours === 720) setInterval('monthly')
        setGrace(data.grace_period_hours ?? 24)
        setTime(data.checkin_time ?? '09:00')
      }catch(e){
        // fail silently — endpoint may not exist in this backend version
      }

      try{
        const c = await axios.get('/api/v1/contacts')
        if(!mounted) return
        const list = c.data || []
        if(list.length){
          const primary = list[0]
          setContactName(primary.name || '')
          setContactEmail(primary.email || '')
        }
      }catch(e){
        // ignore
      }
    })()

    return ()=>{mounted=false}
  },[])

  function intervalToHours(i){
    if(i === 'daily') return 24
    if(i === 'weekly') return 168
    if(i === 'monthly') return 720
    return 24
  }

  async function save(e){
    e.preventDefault()
    setMessage(null)

    // Build settings payload matching backend schema
  const settingsPayload = {
  check_interval_hours: intervalToHours(interval),  
  grace_period_hours: Number(grace),               
  checkin_time: time,                               
  preferred_channel: "email",                        
  auto_alert_enabled: true,                          
  legacy_enabled: false                             
}

    try{
      // Update settings with PUT (backend expects PUT)
      await axios.put('/api/v1/settings', settingsPayload)

      // If user provided an emergency contact, send a separate request to the contacts endpoint
      if(contactName || contactEmail){
        const contactPayload = {
          name: contactName || 'Emergency contact',
          relation: 'emergency',
          email: contactEmail || undefined,
          phone: undefined,
          priority_order: 1,
        }
        // create contact (backend expects POST /contacts)
        await axios.post('/api/v1/contacts', contactPayload)
      }

      setMessage('Saved')
    }catch(err){
      console.error(err)
      setMessage('Save failed')
    }
  }

  return (
    <div>
      <Nav />
      <main className="container-max py-12">
        <div className="max-w-lg mx-auto card p-6 rounded shadow">
          <h2 className="text-lg font-semibold mb-4">Setup your check-ins</h2>
          {message && <div className="text-sm text-sky-700 mb-3">{message}</div>}
          <form onSubmit={save} className="space-y-4">
            <label className="block">
              <span className="text-sm text-gray-600">Check interval</span>
              <select value={interval} onChange={(e)=>setInterval(e.target.value)} className="mt-1 block w-full rounded border border-gray-200 px-3 py-2 bg-white">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </label>

            <FormInput label="Grace period (hours)" type="number" value={grace} onChange={(e)=>setGrace(Number(e.target.value))} />

            <label className="block">
              <span className="text-sm text-gray-600">Preferred check-in time</span>
              <input type="time" value={time} onChange={(e)=>setTime(e.target.value)} className="mt-1 block w-full rounded border border-gray-200 px-3 py-2 bg-white" />
            </label>

            <div className="pt-2">
              <h3 className="text-sm font-medium">Emergency contact</h3>
              <FormInput label="Name" type="text" value={contactName} onChange={(e)=>setContactName(e.target.value)} />
              <FormInput label="Email" type="email" value={contactEmail} onChange={(e)=>setContactEmail(e.target.value)} />
              <p className="text-xs text-gray-500 mt-1">Contacts are created via a separate API call (POST /api/v1/contacts).</p>
            </div>

            <div className="flex justify-end">
              <button className="px-4 py-2 bg-sky-500 text-white rounded">Save</button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
