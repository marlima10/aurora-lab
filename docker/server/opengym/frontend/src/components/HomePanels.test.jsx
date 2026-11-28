// @vitest-environment happy-dom
import React,{act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach,beforeEach,expect,it,vi} from 'vitest'
import HomePanels from './HomePanels.jsx'
import {useStore} from '../store/useStore.js'
import {HOME_PANELS,panelOrder,movePanel} from '../lib/home-panels.js'
import {stampChange,mergeStates} from '../lib/sync-merge.js'
vi.mock('../store/useStore.js',async()=>{const {create}=await import('zustand');return {useStore:create((set,get)=>({S:{},writes:0,update:fn=>{const S=structuredClone(get().S);fn(S);set({S,writes:get().writes+1})}}))}})
globalThis.IS_REACT_ACT_ENVIRONMENT=true
let host,root
const panels=[{id:'agenda',title:'Agenda',content:<div className="card">A</div>},{id:'progress',title:'Progresso',content:<div className="card">P</div>},{id:'metrics',title:'Tempo e calorias',content:<div className="card">T+C</div>}]
beforeEach(()=>{useStore.setState({S:{workouts:[{id:'untouched'}],routines:[{id:'plan'}]},writes:0});host=document.createElement('div');document.body.append(host);root=createRoot(host);act(()=>root.render(<HomePanels panels={panels}/>))})
afterEach(()=>{act(()=>root.unmount());host.remove();vi.restoreAllMocks()})
const button=label=>[...host.querySelectorAll('button')].find(b=>b.getAttribute('aria-label')===label || b.textContent===label)
const click=label=>act(()=>button(label).click())
const order=()=>[...host.querySelectorAll('[data-home-panel]')].map(e=>e.dataset.homePanel)
const event=(node,type,props={})=>act(()=>{const e=new Event(type,{bubbles:true,cancelable:true});Object.assign(e,{pointerId:1,button:0,clientX:100,clientY:200,...props});node.dispatchEvent(e)})
it('sanitizes unknown/duplicate settings and retains hidden panel order',()=>{
 expect(panelOrder(['calories','bogus','calories'])).toEqual(['metrics',...HOME_PANELS.filter(x=>x!=='metrics')]);expect(panelOrder(null)).toEqual(HOME_PANELS)
 const old=['calories','progress'];expect(movePanel(old,'unknown','progress')).toEqual(panelOrder(old));expect(old).toEqual(['calories','progress'])
})
it('moves only layout, keeps workout interactions normal and survives remount',()=>{
 expect(button('Arrastar painel Agenda')).toBeUndefined();click('Organizar painéis');click('Mover Tempo e calorias para cima')
 expect(order()).toEqual(['agenda','metrics','progress']);expect(useStore.getState().S.workouts).toEqual([{id:'untouched'}]);expect(useStore.getState().S.routines).toEqual([{id:'plan'}])
 act(()=>root.unmount());root=createRoot(host);act(()=>root.render(<HomePanels panels={panels}/>));expect(order()).toEqual(['agenda','metrics','progress'])
})
it('keyboard moves and restoring defaults are accessible',()=>{
 click('Organizar painéis');expect(host.querySelector('[role=status]').textContent).toBe('');const handle=button('Arrastar painel Progresso');act(()=>handle.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true})))
 expect(order()).toEqual(['agenda','metrics','progress']);click('Restaurar ordem padrão');expect(order()).toEqual(['agenda','progress','metrics']);expect(button('Mover Agenda para cima').disabled).toBe(true)
})
it('pointer drag previews without writes, commits once on release',()=>{
 click('Organizar painéis');const handle=button('Arrastar painel Progresso');vi.spyOn(document,'elementFromPoint').mockReturnValue(host.querySelector('[data-home-panel="metrics"]'))
 event(handle,'pointerdown');event(handle,'pointermove');expect(useStore.getState().writes).toBe(0);expect(order()).toEqual(['agenda','metrics','progress']);event(handle,'pointerup');expect(useStore.getState().writes).toBe(1)
})
it('cancelled touch/drag keeps the saved order',()=>{
 click('Organizar painéis');const handle=button('Arrastar painel Progresso');vi.spyOn(document,'elementFromPoint').mockReturnValue(host.querySelector('[data-home-panel="metrics"]'))
 event(handle,'pointerdown');event(handle,'pointermove');event(handle,'pointercancel');expect(useStore.getState().writes).toBe(0);expect(order()).toEqual(['agenda','progress','metrics'])
})
it('another profile uses its own order',()=>{
 act(()=>useStore.setState({S:{auroraHomePanels:['calories','agenda']}}));expect(order()[0]).toBe('metrics');act(()=>useStore.setState({S:{auroraHomePanels:['minutes','progress']}}));expect(order()[0]).toBe('metrics')
})
it('native sync preserves layout against an unrelated newer workout',()=>{
 const base={_ts:1,unit:'kg',workouts:[],routines:[],bodyweight:[],customEx:[]};const layout=structuredClone(base);layout.auroraHomePanels=['calories','progress'];layout._ts=stampChange(base,layout,20)
 const garmin=structuredClone(base);garmin.workouts=[{id:'garmin-new',d:'2026-10-21',start:1,entries:[]}];garmin._ts=stampChange(base,garmin,30)
 const merged=mergeStates(layout,garmin);expect(merged.auroraHomePanels).toEqual(['calories','progress']);expect(merged.workouts.map(w=>w.id)).toEqual(['garmin-new'])
})

it('optional native cards leave no empty slot and reappear in their saved position',async()=>{
 const Empty=({show})=>show?<div className="card">Extra</div>:null;
 const rows=show=>[...panels,{id:'recap',title:'Resumo',content:<Empty show={show}/>}];
 await act(async()=>root.render(<HomePanels panels={rows(false)}/>));
 expect(host.querySelector('[data-home-panel="recap"]').hidden).toBe(true);
 click('Organizar painéis');expect(button('Mover Tempo e calorias para baixo').disabled).toBe(true);
 await act(async()=>root.render(<HomePanels panels={rows(true)}/>));
 expect(host.querySelector('[data-home-panel="recap"]').hidden).toBe(false);
 expect(useStore.getState().writes).toBe(0);
});

it.each([
  [['minutes','agenda'],'metrics'],
  [['calories','agenda'],'metrics'],
  [['progress','calories','agenda','minutes'],'progress'],
  [['progress','agenda'],'progress'],
])('migrates legacy order %j without duplicating the combined panel',(saved,first)=>{
  const order=panelOrder(saved)
  expect(order[0]).toBe(first)
  expect(order.filter(id=>id==='metrics')).toHaveLength(1)
})
it('hides both metrics together and applies the preference per profile',()=>{
  click('Organizar painéis');click('Ocultar Tempo e calorias')
  expect(order()).not.toContain('metrics')
  expect(useStore.getState().S.auroraMetricsHidden).toBe(true)
  act(()=>useStore.setState({S:{auroraHomePanels:['calories','agenda']}}))
  expect(order()[0]).toBe('metrics')
})
