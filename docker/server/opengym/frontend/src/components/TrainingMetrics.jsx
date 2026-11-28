import CardHead from './CardHead.jsx'
import { useId, useMemo, useState } from 'react'
import LineChart from './LineChart.jsx'
import { Segmented } from './ui.jsx'
import { trainingMetrics } from '../lib/training-metrics.js'
import './training-metrics.css'

const number = value => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(value)
const choices = [{ value: 7, label: '7 dias' }, { value: 30, label: '30 dias' }, { value: 90, label: '90 dias' }, { value: 0, label: 'Todos' }]
const metrics = [
  { key: 'minutes', label: 'Tempo', title: 'Tempo de exercício', icon: 'clock', unit: 'min', color: 'var(--blue)', empty: 'Nenhum tempo de exercício registrado neste período.' },
  { key: 'calories', label: 'Calorias', title: 'Calorias gastas', icon: 'flame', unit: 'kcal', color: 'var(--orange)', empty: 'Sem calorias do Garmin neste período' },
]

function MetricContent({ metric, data }) {
  const points = data[metric.key], sum = points.reduce((total, point) => total + point.y, 0)
  const isCalories = metric.key === 'calories'
  return <>
    {!points.length && <p className="small muted" role="status">{metric.empty}</p>}
    {points.length > 0 && <>
      <p className="aurora-metric-total">{number(sum)} <span className="muted small">{metric.unit} no período</span></p>
      <div className="chart" role="img" aria-label={metric.title + ': ' + number(sum) + ' ' + metric.unit + '. Totais por dia.'}>
        <LineChart points={points} h={150} unit={metric.unit} color={metric.color} />
      </div>
      <details className="small"><summary>Ver valores por dia</summary><div className="aurora-metric-table"><table><caption>{metric.title} por dia</caption><thead><tr><th>Data</th><th>{metric.unit}</th></tr></thead><tbody>{points.map(point => <tr key={point.d}><td>{point.d.split('-').reverse().join('/')}</td><td>{number(point.y)}</td></tr>)}</tbody></table></div></details>
    </>}
    <details className="small"><summary>Como é calculado</summary>
      <p>{isCalories ? data.calorieCount : data.durationCount} de {data.workoutsCount} treinos com dados. Os totais usam a data local do treino e cada sessão conta uma vez. Datas inválidas ou futuras ficam de fora.</p>
      <p>{isCalories ? 'Somente calorias informadas pelo Garmin, sem estimativas. Ausência de calorias não vira zero. Zeros reais são aceitos.' : 'A duração vai do início ao fim da sessão, incluindo pausas. Sem esses horários, somam-se séries concluídas de cardio ou tempo.'}</p>
    </details>
  </>
}

export default function TrainingMetrics({ S, combined = false }) {
  const [days, setDays] = useState(30), [tab, setTab] = useState(0)
  const id = useId()
  const today = new Date().toLocaleDateString('sv-SE')
  const data = useMemo(() => trainingMetrics(S.workouts, days, new Date(today + 'T12:00:00')), [S.workouts, days, today])
  const period = <div className="aurora-metrics-range"><span className="small muted">Período</span><Segmented of="Período de treino" value={days} onChange={setDays} options={choices} /></div>
  if (combined) return <section className="card aurora-metric" aria-label="Tempo e calorias">
    <CardHead title="Tempo e calorias" eyebrow="Seu histórico" icon={metrics[tab].icon} />
    <div className="aurora-metric-tabs" role="tablist" aria-label="Métrica">
      {metrics.map((metric, index) => <button key={metric.key} type="button" role="tab" id={id + '-' + index}
        aria-selected={tab === index} aria-controls={id + '-panel-' + index} tabIndex={tab === index ? 0 : -1}
        onClick={() => setTab(index)} onKeyDown={event => {
          if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
          event.preventDefault()
          const next = event.key === 'Home' ? 0 : event.key === 'End' ? metrics.length - 1 : (index + 1) % metrics.length
          setTab(next)
          document.getElementById(id + '-' + next)?.focus()
        }}>{metric.label}</button>)}
    </div>
    {period}
    {metrics.map((metric, index) => <div key={metric.key} role="tabpanel" id={id + '-panel-' + index} aria-labelledby={id + '-' + index} hidden={index !== tab}>
      {index === tab && <MetricContent metric={metric} data={data} />}
    </div>)}
  </section>

  return <>{period}<div className="aurora-metrics-grid">
    {metrics.map(metric => <section className="card aurora-metric" aria-label={metric.title} key={metric.key}>
      <CardHead title={metric.title} eyebrow="Seu histórico" icon={metric.icon} />
      <MetricContent metric={metric} data={data} />
    </section>)}
  </div></>
}
