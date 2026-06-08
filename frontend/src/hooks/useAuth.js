import { useState } from 'react'

// Very small placeholder hook to represent auth state if needed.
export default function useAuth(){
  const [user, setUser] = useState(null)
  return {user, setUser}
}
