import React, {useState} from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from '../api/axios'
import FormInput from '../components/FormInput'
import Nav from '../components/Nav'

export default function Login(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  async function submit(e){
    e.preventDefault()
    setError(null)
    try{
      await axios.post('/api/v1/auth/login', {email, password})
      // backend sets httpOnly cookie; navigate to dashboard
      navigate('/dashboard')
    }catch(err){
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div>
      <Nav />
      <main className="container-max py-16">
        <div className="max-w-md mx-auto card p-6 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">Log in</h2>
          {error && <div className="text-sm text-red-600 mb-3">{error}</div>}
          <form onSubmit={submit} className="space-y-4">
            <FormInput label="Email" type="email" value={email} onChange={(e)=>setEmail(e.target.value)} required />
            <FormInput label="Password" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} required />
            <div className="flex justify-between items-center">
              <button className="px-4 py-2 bg-sky-500 text-white rounded">Sign in</button>
              <Link to="/signup" className="text-sm text-slate-600">Create account</Link>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
