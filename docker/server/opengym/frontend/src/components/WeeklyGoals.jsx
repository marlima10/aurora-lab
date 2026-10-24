import { useEffect, useState } from 'react'
import { useStore } from '../store/useStore.js'
import { validGoals, weeklyProgress, GOAL_LIMITS } from '../lib/weekly-goals.js'
import './aurora-upgrades.css'
const labels = { workouts: 'Treinos', minutes: 'Minutos', calories: 'Calorias (kcal)' }
const fmt = n => new Intl.NumberFormat('pt-BR',{maximumFractionDigits:1}).format(n)
export default function WeeklyGoals({ S }) {
  const uid = useStore(s => s.user?.id)
  useEffect(()=>{setEditing(false);setMessage('')},[uid])
  const goals = validGoals(S.auroraWeeklyGoals)
  const [editing,setEditing] = useState(false), [message,setMessage] = useState('')
  const progress = weeklyProgress(S.workouts)
  function save(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const next = validGoals(Object.fromEntries(Object.keys(labels).map(k=>[k,Number(form.get(k))])))
    if (!next) { setMessage('Revise os limites das metas.');return }
    useStore.getState().update(state => { state.auroraWeeklyGoals = next })
    setEditing(false);setMessage('Metas atualizadas no perfil; acompanham a sincronização do openGym.')
  }
  return <section className="card aurora-upgrade" aria-label="Metas semanais">
    <h2>Metas semanais</h2><p className="small muted">Segunda-feira até hoje · {progress.first.split('-').reverse().join('/')}. Treinos concluídos; cada sessão conta uma vez.</p>
    {goals && Object.entries(labels).map(([key,label]) => <div className="aurora-goal" key={key}>
      <label htmlFor={'goal-meter-'+key}>{label}: {fmt(progress[key])}{goals[key] > 0 ? ' / '+fmt(goals[key]) : ' · sem meta'}</label>
      {goals[key] > 0 && <progress id={'goal-meter-'+key} max={goals[key]} value={Math.min(progress[key],goals[key])} aria-label={label} />}
    </div>)}
    {!goals && <p className="muted">Defina suas metas de treinos, tempo e calorias.</p>}
    <p className="small muted">Duração disponível em {progress.durationCount} e calorias em {progress.calorieCount} de {progress.workouts} treinos. Calorias ausentes não são estimadas.</p>
    {!editing ? <button className="btn" onClick={()=>{setEditing(true);setMessage('')}}>Editar metas</button> : <form onSubmit={save} className="aurora-goal-form">
      {Object.entries(labels).map(([key,label])=><label key={key}>{label}<input name={key} type="number" inputMode="numeric" min="0" max={GOAL_LIMITS[key]} step="1" required defaultValue={goals?.[key] ?? 0}/></label>)}
      <p className="small muted">Use zero para deixar uma meta desativada. As metas são pessoais, sem alterar sua agenda de treinos.</p>
      <div className="aurora-actions"><button className="btn" type="submit">Salvar metas</button><button className="btn" type="button" onClick={()=>setEditing(false)}>Cancelar</button></div>
    </form>}
    <p role="status" className="small muted">{message}</p>
  </section>
}
