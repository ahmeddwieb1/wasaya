export function niceDatetime(src){
  if(!src) return null
  try{
    const d = new Date(src)
    return d.toLocaleString()
  }catch(e){
    return src
  }
}
