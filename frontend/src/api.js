const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options={}) {
  const res = await fetch(`${API_BASE}${path}`, {headers:{'Content-Type':'application/json',...(options.headers||{})}, ...options})
  if (!res.ok) { let msg=`HTTP ${res.status}`; try { const j=await res.json(); msg=j.detail||msg } catch {} throw new Error(msg) }
  return res
}
export async function json(path, options={}) { return (await request(path,options)).json() }
export const api = {
  health:()=>json('/health'),
  indicator:(country,indicator,start=2000,end=2025)=>json(`/api/economy/${country}/${indicator}?start_year=${start}&end_year=${end}`),
  indicators:()=>json('/api/economy/indicators'),
  forecast:(country,indicator,horizon=5,model='autoreg')=>json(`/api/forecast/${country}/${indicator}?start_year=1990&end_year=2025&horizon=${horizon}&model=${model}`),
  simulate:(body)=>json('/api/scenario/simulate',{method:'POST',body:JSON.stringify(body)}),
  compareScenarios:(scenarios)=>json('/api/scenario/compare',{method:'POST',body:JSON.stringify({scenarios})}),
  sectorImpact:(body)=>json('/api/scenario/sector-impact',{method:'POST',body:JSON.stringify(body)}),
  variables:()=>json('/api/scenario/variables'),
  agent:(query)=>json('/api/agent/query',{method:'POST',body:JSON.stringify({query})}),
  scenarios:(country='',limit=25)=>json(`/api/scenarios?limit=${limit}${country?`&country=${country}`:''}`),
  scenario:(id)=>json(`/api/scenarios/${id}`),
  regional:(countries,indicator='gdp_growth')=>json(`/api/insights/regional-comparison?countries=${countries.join(',')}&indicator=${indicator}&start_year=2000&end_year=2025`),
  sectors:(country)=>json(`/api/insights/sector-comparison/${country}?start_year=2000&end_year=2025`),
  reportUrl:(id)=>`${API_BASE}/api/reports/${id}.pdf`,
}
export function latest(payload){ const a=payload?.observations||[]; return a.length?a[a.length-1]:null }
export function val(obs){ return obs?.value ?? obs?.Value ?? null }
export function year(obs){ return obs?.year ?? obs?.date ?? obs?.Year ?? '' }
