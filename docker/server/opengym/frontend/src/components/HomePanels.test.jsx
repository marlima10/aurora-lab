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
const panels=[{id:'agenda',title:'Agenda',content:<div className="card">A</div>},{id:'progress',title:'Progresso',content:<div className="card">P</div>},{id:'minutes',title:'Tempo',content:<div className="card">T</div>},{id:'calories',title:'Calorias',content:<div className="card">C</div>}]
beforeEach(()=>{useStore.setState({S:{workouts:[{id:'untouched'}],routines:[{id:'plan'}]},writes:0});host=document.createElement('div');document.body.append(host);root=createRoot(host);act(()=>root.render(<HomePanels panels={panels}/>))})
afterEach(()=>{act(()=>root.unmount());host.remove();vi.restoreAllMocks()})
const button=label=>[...host.querySelectorAll('button')].find(b=>b.getAttribute('aria-label')===label || b.textContent===label)
const click=label=>act(()=>button(label).click())
const order=()=>[...host.querySelectorAll('[data-home-panel]')].map(e=>e.dataset.homePanel)
const event=(node,type,props={})=>act(()=>{const e=new Event(type,{bubbles:true,cancelable:true});Object.assign(e,{pointerId:1,button:0,clientX:100,clientY:200,...props});node.dispatchEvent(e)})
it('sanitizes unknown/duplicate settings and retains hidden panel order',()=>{
 expect(panelOrder(['calories','bogus','calories'])).toEqual(['calories',...HOME_PANELS.filter(x=>x!=='calories')]);expect(panelOrder(null)).toEqual(HOME_PANELS)
 const old=['calories','progress'];expect(movePanel(old,'unknown','progress')).toEqual(panelOrder(old));expect(old).toEqual(['calories','progress'])
})
it('moves only layout, keeps workout interactions normal and survives remount',()=>{
 expect(button('Arrastar painel Agenda')).toBeUndefined();click('Organizar painéis');click('Mover Calorias para cima')
 expect(order()).toEqual(['agenda','progress','calories','minutes']);expect(useStore.getState().S.workouts).toEqual([{id:'untouched'}]);expect(useStore.getState().S.routines).toEqual([{id:'plan'}])
 act(()=>root.unmount());root=createRoot(host);act(()=>root.render(<HomePanels panels={panels}/>));expect(order()).toEqual(['agenda','progress','calories','minutes'])
})
it('keyboard moves and restoring defaults are accessible',()=>{
 click('Organizar painéis');expect(host.querySelector('[role=status]').textContent).toBe('');const handle=button('Arrastar painel Progresso');act(()=>handle.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true})))
 expect(order()).toEqual(['agenda','minutes','progress','calories']);click('Restaurar ordem padrão');expect(order()).toEqual(['agenda','progress','minutes','calories']);expect(button('Mover Agenda para cima').disabled).toBe(true)
})
it('pointer drag previews without writes, commits once on release',()=>{
 click('Organizar painéis');const handle=button('Arrastar painel Progresso');vi.spyOn(document,'elementFromPoint').mockReturnValue(host.querySelector('[data-home-panel="calories"]'))
 event(handle,'pointerdown');event(handle,'pointermove');expect(useStore.getState().writes).toBe(0);expect(order()).toEqual(['agenda','minutes','calories','progress']);event(handle,'pointerup');expect(useStore.getState().writes).toBe(1)
})
it('cancelled touch/drag keeps the saved order',()=>{
 click('Organizar painéis');const handle=button('Arrastar painel Progresso');vi.spyOn(document,'elementFromPoint').mockReturnValue(host.querySelector('[data-home-panel="calories"]'))
 event(handle,'pointerdown');event(handle,'pointermove');event(handle,'pointercancel');expect(useStore.getState().writes).toBe(0);expect(order()).toEqual(['agenda','progress','minutes','calories'])
})
it('another profile uses its own order',()=>{
 act(()=>useStore.setState({S:{auroraHomePanels:['calories','agenda']}}));expect(order()[0]).toBe('calories');act(()=>useStore.setState({S:{auroraHomePanels:['minutes','progress']}}));expect(order()[0]).toBe('minutes')
})
it('native sync preserves layout against an unrelated newer workout',()=>{
 const base={_ts:1,unit:'kg',workouts:[],routines:[],bodyweight:[],customEx:[]};const layout=structuredClone(base);layout.auroraHomePanels=['calories','progress'];layout._ts=stampChange(base,layout,20)
 const garmin=structuredClone(base);garmin.workouts=[{id:'garmin-new',d:'2026-10-21',start:1,entries:[]}];garmin._ts=stampChange(base,garmin,30)
 const merged=mergeStates(layout,garmin);expect(merged.auroraHomePanels).toEqual(['calories','progress']);expect(merged.workouts.map(w=>w.id)).toEqual(['garmin-new'])
})
