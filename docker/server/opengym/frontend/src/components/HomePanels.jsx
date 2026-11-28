import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useStore } from '../store/useStore.js'
import { panelOrder, movePanel } from '../lib/home-panels.js'
import './home-panels.css'

export default function HomePanels({ panels }) {
  const saved = useStore(s => s.S.auroraHomePanels)
  const metricsHidden = useStore(s => s.S.auroraMetricsHidden === true)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(null)
  const [dragging, setDragging] = useState(null)
  const [message, setMessage] = useState('')
  const container = useRef(null)
  const [empty, setEmpty] = useState([])
  const gesture = useRef(null)
  const order = draft || panelOrder(saved)
  const visible = order.filter(id => !(id === 'metrics' && metricsHidden) && panels.some(panel => panel.id === id && panel.content))
  const displayed = visible.filter(id => !empty.includes(id))
  useLayoutEffect(() => {
    const refresh = () => {
      const next = [...(container.current?.querySelectorAll('[data-home-content]') || [])]
        .filter(node => !node.childElementCount && !node.textContent.trim())
        .map(node => node.getAttribute('data-home-content')).sort()
      setEmpty(old => JSON.stringify(old) === JSON.stringify(next) ? old : next)
    }
    refresh()
    const observer = new MutationObserver(refresh)
    if (container.current) observer.observe(container.current, { childList: true, subtree: true, characterData: true })
    return () => observer.disconnect()
  }, [panels])

  const commit = (next, title) => {
    if (JSON.stringify(next) !== JSON.stringify(panelOrder(saved))) useStore.getState().update(s => { s.auroraHomePanels = next })
    setMessage(title + ': ordem atualizada.');setDraft(null)
  }
  const move = (id, direction) => {
    const index = displayed.indexOf(id), target = displayed[index + direction]
    if (target) commit(movePanel(saved, id, target), panels.find(p => p.id === id).title)
  }
  const down = (event, id) => {
    if (!editing || event.button > 0) return
    event.preventDefault()
    event.currentTarget.focus({ preventScroll: true })
    gesture.current = { id, pointerId: event.pointerId, order: panelOrder(saved) }
    setDraft(gesture.current.order);setDragging(id);setMessage('Arrastando ' + panels.find(p => p.id === id).title)
  }
  const motion = event => {
    const current = gesture.current
    if (!current || current.pointerId !== event.pointerId) return
    const over = document.elementFromPoint?.(event.clientX, event.clientY)?.closest('[data-home-panel]')?.getAttribute('data-home-panel')
    if (over && over !== current.id && displayed.includes(over)) {
      current.order = movePanel(current.order, current.id, over);setDraft(current.order)
    }
    if (event.clientY < 75) window.scrollBy(0, -18)
    else if (event.clientY > window.innerHeight - 90) window.scrollBy(0, 18)
  }
  const finish = (event, cancelled = false) => {
    const current = gesture.current
    if (!current || current.pointerId !== event.pointerId) return
    gesture.current = null;setDragging(null)
    if (cancelled) { setDraft(null);setMessage('Arraste cancelado.');return }
    commit(current.order, panels.find(p => p.id === current.id).title)
  }
  const cancel = () => { const active = gesture.current;gesture.current = null;setDraft(null);setDragging(null);setMessage(active ? 'Arraste cancelado.' : '') }
  // Listen on the window: moving a keyed panel in the DOM releases pointer capture in browsers.
  // The ref carries the preview order, so one release commits once even after several reorders.
  useEffect(() => {
    if (!dragging) return
    const cancelled = event => finish(event, true)
    const escape = event => { if (event.key === 'Escape') cancel() }
    window.addEventListener('pointermove', motion)
    const dropped = event => finish(event)
    window.addEventListener('pointerup', dropped)
    window.addEventListener('pointercancel', cancelled)
    window.addEventListener('keydown', escape)
    window.addEventListener('blur', cancel)
    return () => {
      window.removeEventListener('pointermove', motion)
      window.removeEventListener('pointerup', dropped)
      window.removeEventListener('pointercancel', cancelled)
      window.removeEventListener('keydown', escape)
      window.removeEventListener('blur', cancel)
    }
  }, [dragging])
  return <section ref={container} className="aurora-home-panels" aria-label="Painéis da página inicial">
    <div className="aurora-arrange-toolbar">
      <button className="aurora-arrange-toggle" aria-pressed={editing} onClick={() => { cancel();setEditing(v => !v) }}>{editing ? 'Concluir organização' : 'Organizar painéis'}</button>
      {editing && <button onClick={() => commit(panelOrder(), 'Layout padrão')}>Restaurar ordem padrão</button>}
      {editing && panels.some(panel => panel.id === 'metrics') && <button onClick={() => {
        useStore.getState().update(state => { state.auroraMetricsHidden = !metricsHidden })
        setMessage(metricsHidden ? 'Tempo e calorias exibidos.' : 'Tempo e calorias ocultos.')
      }}>{metricsHidden ? 'Exibir Tempo e calorias' : 'Ocultar Tempo e calorias'}</button>}
    </div>
    {editing && <p className="small muted">Arraste pela alça ⠿ ou use as setas para mover. No teclado, use ↑ e ↓ na alça; Esc cancela o arraste. A ordem fica no seu perfil e acompanha a sincronização do openGym.</p>}
    <p className="aurora-panel-announcement" role="status" aria-live="polite">{message}</p>
    {visible.map(id => {
      const index = displayed.indexOf(id)
      const panel = panels.find(p => p.id === id)
      return <section key={id} hidden={empty.includes(id)} data-home-panel={id} aria-label={panel.title} className={'aurora-home-panel' + (editing ? ' arranging' : '') + (dragging === id ? ' dragging' : '')}>
        {editing && <div className="aurora-panel-handlebar">
          <button className="aurora-panel-handle" aria-label={'Arrastar painel ' + panel.title} onPointerDown={e => down(e, id)}
            onKeyDown={e => { if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault();move(id, e.key === 'ArrowUp' ? -1 : 1) } else if (e.key === 'Escape') cancel() }}>⠿ <span>{panel.title}</span></button>
          <button disabled={index === 0} aria-label={'Mover ' + panel.title + ' para cima'} onClick={() => move(id, -1)}>↑</button>
          <button disabled={index === displayed.length - 1} aria-label={'Mover ' + panel.title + ' para baixo'} onClick={() => move(id, 1)}>↓</button>
        </div>}
        <div className="aurora-home-content" data-home-content={id}>{panel.content}</div>
      </section>
    })}
  </section>
}
