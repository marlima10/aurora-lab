// Daily totals use the workout local date; missing metrics are never converted to zero.
export function metricNumber(value, max = Infinity) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= max ? value : null
}
export function workoutMinutes(workout) {
  const start = metricNumber(workout.start), end = metricNumber(workout.end)
  if (start !== null && end !== null && end > start && end - start <= 604800000) return (end - start) / 60000
  let minutes = 0, found = false
  for (const entry of workout.entries || []) for (const row of entry.sets || []) {
    if (row.done !== true) continue
    const value = entry.mode === 'cardio' ? metricNumber(row.min, 10080) : entry.mode === 'time' ? metricNumber(row.sec, 604800) : null
    if (value !== null) { minutes += entry.mode === 'time' ? value / 60 : value; found = true }
  }
  return found ? minutes : null
}
export function trainingMetrics(workouts, days = 30, today = new Date()) {
  const cutoff = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 12)
  const last = +cutoff; cutoff.setDate(cutoff.getDate() - Math.max(0, days - 1))
  const first = days ? +cutoff : -Infinity
  const totals = new Map(), seen = new Set()
  let workoutsCount = 0, calorieCount = 0, durationCount = 0
  for (const workout of workouts || []) {
    if (!workout || seen.has(workout.id)) continue
    const d = workout.d
    if (typeof d !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(d)) continue
    const date = new Date(d + 'T12:00:00')
    const local = date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0')
    if (local !== d || +date < first || +date > last) continue
    seen.add(workout.id);workoutsCount++
    const minutes = workoutMinutes(workout), calories = metricNumber(workout.garminActivity?.calories, 200000)
    const total = totals.get(d) || { d, t: +date, minutes: 0, calories: 0, durationCount: 0, calorieCount: 0 }
    if (minutes !== null) { total.minutes += minutes; total.durationCount++; durationCount++ }
    if (calories !== null) { total.calories += calories; total.calorieCount++; calorieCount++ }
    totals.set(d, total)
  }
  const daily = [...totals.values()].sort((a, b) => a.t - b.t)
  return {
    minutes: daily.filter(d => d.durationCount).map(d => ({ t: d.t, d: d.d, y: d.minutes })),
    calories: daily.filter(d => d.calorieCount).map(d => ({ t: d.t, d: d.d, y: d.calories })),
    workoutsCount, calorieCount, durationCount,
  }
}
