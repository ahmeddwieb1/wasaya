import axios from 'axios'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default instance
