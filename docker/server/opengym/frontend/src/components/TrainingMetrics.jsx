import { useMemo, useState } from 'react'
import LineChart from './LineChart.jsx'
import { Segmented } from './ui.jsx'
import { trainingMetrics } from '../lib/training-metrics.js'
import './training-metrics.css'

const number = value => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(value)
export default function TrainingMetrics({ S }) {
  const [days, setDays] = useState(30)
  const today = new Date().toLocaleDateString('sv-SE')
  const data = useMemo(() => trainingMetrics(S.workouts, days, new Date(today + 'T12:00:00')), [S.workouts, days, today])
  const choices = [{value: 7, label: '7 dias'}, {value: 30, label: '30 dias'}, {value: 90, label: '90 dias'}, {value: 0, label: 'Todos'}]
  return <>
    <div className="aurora-metrics-range">
      <span className="small muted">Período de tempo e calorias</span>
      <Segmented value={days} onChange={setDays} options={choices} />
    </div>
    <div className="aurora-metrics-grid">
      {[{key: 'minutes', title: 'Tempo de exercício', unit: 'min', count: data.durationCount, color: 'var(--blue)', empty: 'Nenhum tempo de exercício registrado neste período.'},
        {key: 'calories', title: 'Calorias gastas', unit: 'kcal', count: data.calorieCount, color: 'var(--orange)', empty: 'Sem calorias informadas pelo Garmin neste período.'}].map(metric => {
        const points = data[metric.key], sum = points.reduce((total, point) => total + point.y, 0)
        return <section className="card aurora-metric" aria-label={metric.title} key={metric.key}>
          <h2>{metric.title}</h2>
          <div className="aurora-metric-total">{points.length ? number(sum) : '—'} <span className="muted small">{metric.unit} no período</span></div>
          {points.length ? <>
            <div className="chart" role="img" aria-label={metric.title + ': ' + number(sum) + ' ' + metric.unit + '. Totais por dia.'}>
              <LineChart points={points} h={150} unit={metric.unit} color={metric.color} />
            </div>
            <details className="small"><summary>Ver valores por dia</summary><div className="aurora-metric-table"><table><caption>{metric.title} por dia</caption><thead><tr><th>Data</th><th>{metric.unit}</th></tr></thead><tbody>{points.map(point => <tr key={point.d}><td>{point.d.split('-').reverse().join('/')}</td><td>{number(point.y)}</td></tr>)}</tbody></table></div></details>
          </> : <p className="muted small" role="status">{metric.empty}</p>}
          <p className="small muted">{metric.count} de {data.workoutsCount} treinos com {metric.key === 'minutes' ? 'duração' : 'calorias'}. Totais por dia.{metric.key === 'calories' ? ' Valores informados pelo Garmin; sem estimativas. Dias sem calorias não são contados como zero.' : ' Duração da sessão; inclui pausas quando fazem parte do registro.'}</p>
        </section>
      })}
    </div>
    <p className="small muted"><a href="https://github.com/marlima10/aurora-lab/tree/main/docker/server/opengym" target="_blank" rel="noopener noreferrer">Código desta versão</a></p>
  </>
}
