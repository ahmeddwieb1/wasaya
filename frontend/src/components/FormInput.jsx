import React from 'react'

export default function FormInput({label, ...props}){
  return (
    <label className="block">
      <span className="text-sm text-gray-600">{label}</span>
      <input className="mt-1 block w-full rounded border border-gray-200 px-3 py-2 bg-white" {...props} />
    </label>
  )
}
