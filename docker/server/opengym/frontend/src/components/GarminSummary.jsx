import { useEffect, useState } from 'react'
import './aurora-upgrades.css'
export default function GarminSummary() {
  const [state,setState] = useState(null),[error,setError] = useState(''),[pending,setPending] = useState(false)
  useEffect(()=>{
    const controller = new AbortController()
    async function refresh() {
      if (document.hidden) return
      try {
        const response = await fetch('/garmin/status',{credentials:'same-origin',cache:'no-store',signal:controller.signal})
        if (!response.ok) throw Error(response.status === 401 ? 'Entre no perfil para consultar o Garmin.' : 'Garmin indisponível. Tente novamente em instantes.')
        const value = await response.json();if (!controller.signal.aborted) {setState(value);setError('')}
      } catch (e) { if (!controller.signal.aborted) setError(e.message) }
    }
    refresh();const timer=setInterval(refresh,30000)
    document.addEventListener('visibilitychange',refresh)
    return ()=>{controller.abort();clearInterval(timer);document.removeEventListener('visibilitychange',refresh)}
  },[])
  async function sync() {
    setPending(true);setError('')
    try {
      const response = await fetch('/garmin/sync',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'})
      const value = await response.json()
      if (!response.ok) throw Error(value.error || 'Não foi possível iniciar a consulta.')
      setState(old=>({...old,busy:true}))
    } catch (e) { setError(e.message) }
    finally {setPending(false)}
  }
  const auto=state?.auto || {}, busy=state?.busy || pending
  const date = value => value ? new Date(value).toLocaleString('pt-BR') : 'Ainda não realizada'
  return <section className="card aurora-upgrade" aria-label="Sincronização Garmin">
    <h2>Garmin</h2><p>{!state ? 'Consultando sincronização…' : state.connected ? auto.enabled ? 'Ativa · últimos 5 treinos a cada hora' : 'Conectado · atualização automática pausada' : 'Conecte sua conta Garmin'}</p>
    {state && <><dl className="aurora-sync-details"><dt>Última consulta</dt><dd>{date(auto.last_run)}</dd><dt>Resultado</dt><dd>{busy ? 'Consulta em andamento…' : auto.last_status === 'error' ? 'Falhou' : auto.last_run ? `${auto.last_added || 0} importado(s) · ${auto.last_skipped || 0} já existente(s)` : 'Aguardando primeira consulta'}</dd><dt>Próxima consulta</dt><dd>{auto.enabled && auto.next_run ? date(auto.next_run*1000) : 'Sem agendamento'}</dd></dl>
    {auto.last_status === 'error' && <p role="alert">{auto.last_error || 'Falha na última consulta. Abra a conexão Garmin para conferir.'}</p>}</>}
    {error && <p role="alert">{error}</p>}
    <div className="aurora-actions"><button className="btn" onClick={sync} disabled={!auto.enabled || busy}>{busy ? 'Consultando…' : 'Sincronizar agora'}</button><a href="/garmin/">Abrir conexão Garmin</a></div>
    <p className="small muted">Não duplica treinos já importados. O resumo é atualizado a cada 30 segundos enquanto esta página estiver aberta.</p>
  </section>
}
