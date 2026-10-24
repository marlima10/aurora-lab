import { trainingMetrics } from './training-metrics.js'
export const GOAL_LIMITS = { workouts: 100, minutes: 10080, calories: 100000 }
export function validGoals(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return null
  const goals = {}
  for (const [key, max] of Object.entries(GOAL_LIMITS)) {
    const value = input[key]
    if (!Number.isInteger(value) || value < 0 || value > max) return null
    goals[key] = value
  }
  return goals
}
export function weeklyProgress(workouts, today = new Date()) {
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 12)
  monday.setDate(monday.getDate() - (monday.getDay() + 6) % 7)
  const date = d => d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0')
  const first = date(monday), last = date(today)
  const data = trainingMetrics((workouts || []).filter(w => w && w.d >= first && w.d <= last), 0, today)
  return { first, last, workouts: data.workoutsCount, minutes: data.minutes.reduce((s,p)=>s+p.y,0), calories: data.calories.reduce((s,p)=>s+p.y,0), durationCount: data.durationCount, calorieCount: data.calorieCount }
}
