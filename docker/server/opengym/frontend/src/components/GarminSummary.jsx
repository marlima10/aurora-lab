import CardHead from './CardHead.jsx'
import { useCallback, useEffect, useRef, useState } from 'react'
import './aurora-upgrades.css'

const formatDate = value => value ? new Date(value).toLocaleString('pt-BR') : 'Ainda não realizada'

export default function GarminSummary() {
  const [result, setResult] = useState({ kind: 'loading' })
  const [syncError, setSyncError] = useState('')
  const [pending, setPending] = useState(false)
  const request = useRef(null)

  const refresh = useCallback(async () => {
    if (document.hidden || request.current) return
    const controller = new AbortController()
    request.current = controller
    try {
      const response = await fetch('/garmin/status', {
        credentials: 'same-origin', cache: 'no-store', signal: controller.signal,
      })
      const result = response.status === 401 ? { kind: 'signed-out' }
        : response.ok ? { kind: 'ready', value: await response.json() } : { kind: 'error' }
      if (!controller.signal.aborted) setResult(result)
    } catch {
      if (!controller.signal.aborted) setResult({ kind: 'error' })
    } finally {
      if (request.current === controller) request.current = null
    }
  }, [])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 30000)
    document.addEventListener('visibilitychange', refresh)
    return () => {
      request.current?.abort()
      request.current = null
      clearInterval(timer)
      document.removeEventListener('visibilitychange', refresh)
    }
  }, [refresh])

  async function sync() {
    setPending(true)
    setSyncError('')
    try {
      const response = await fetch('/garmin/sync', {
        method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}',
      })
      if (response.status === 401) {
        setResult({ kind: 'signed-out' })
        return
      }
      const value = await response.json()
      if (!response.ok) throw Error(value.error || 'Não foi possível iniciar a consulta.')
      request.current?.abort()
      request.current = null
      setResult(old => old.kind === 'ready' ? { ...old, value: { ...old.value, busy: true } } : old)
    } catch (error) {
      setSyncError(error.message)
    } finally {
      setPending(false)
    }
  }

  const state = result.value, auto = state?.auto || {}, busy = state?.busy || pending
  const connected = result.kind === 'ready' && state.connected
  const reason = result.kind === 'loading' ? 'Aguarde a consulta inicial.'
    : result.kind === 'signed-out' ? 'Entre no perfil para sincronizar.'
    : result.kind === 'error' ? 'Consulte o estado novamente.'
    : !connected ? 'Conecte sua conta Garmin.'
    : busy ? 'Aguarde a consulta em andamento.'
    : !auto.enabled ? 'Ative a atualização automática na conexão Garmin.' : ''
  const alert = result.kind === 'signed-out' ? 'Entre no perfil para consultar o Garmin.'
    : result.kind === 'error' ? 'Garmin indisponível.'
    : connected && !busy ? syncError || (auto.last_status === 'error' ? auto.last_error || 'Falha na última consulta.' : '') : ''
  return <section className="card aurora-upgrade" aria-label="Sincronização Garmin">
    <CardHead title="Garmin" eyebrow="Conector AuroraLAB" icon="heart" />
    {result.kind === 'loading' && <p role="status">Consultando sincronização…</p>}
    {result.kind === 'ready' && !connected && <p role="status">Garmin desconectado.</p>}
    {connected && <dl className="aurora-sync-details">
      <dt>Última consulta</dt><dd>{formatDate(auto.last_run)}</dd>
      <dt>Resultado</dt><dd>{busy ? 'Consulta em andamento…' : auto.last_status === 'error' ? 'Falhou' : auto.last_run ? `${auto.last_added || 0} importado(s) · ${auto.last_skipped || 0} já existente(s)` : 'Aguardando primeira consulta'}</dd>
      <dt>Próxima consulta</dt><dd>{auto.enabled && auto.next_run ? formatDate(auto.next_run * 1000) : 'Sem agendamento'}</dd>
    </dl>}
    {alert && <p role="alert">{alert}</p>}
    {reason && <p className="small muted">{reason}</p>}
    <div className="aurora-actions">
      <button className="btn" onClick={sync} disabled={Boolean(reason)}>Sincronizar agora</button>
      {result.kind === 'error' && <button className="btn" onClick={refresh}>Tentar de novo</button>}
      {(connected || result.kind === 'ready') && <a href="/garmin/">Abrir conexão Garmin</a>}
    </div>
    <details className="small"><summary>Como é calculado</summary>
      <p>Quando ativa, a atualização automática consulta os últimos cinco treinos a cada hora. A importação ignora treinos já registrados. Com a página aberta, este resumo é consultado a cada 30 segundos.</p>
    </details>
  </section>
}
