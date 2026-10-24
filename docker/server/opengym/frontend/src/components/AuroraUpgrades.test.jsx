// @vitest-environment happy-dom
import React,{act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach,beforeEach,expect,it,vi} from 'vitest'
import WeeklyGoals from './WeeklyGoals.jsx'
import GarminSummary from './GarminSummary.jsx'
import {validGoals,weeklyProgress} from '../lib/weekly-goals.js'
import {useStore} from '../store/useStore.js'
import {mergeStates,stampChange} from '../lib/sync-merge.js'
vi.mock('../store/useStore.js',async()=>{const {create}=await import('zustand');return {useStore:create((set,get)=>({S:{},user:{id:'one'},update:fn=>{const S=structuredClone(get().S);fn(S);set({S})}}))}})
globalThis.IS_REACT_ACT_ENVIRONMENT=true
let host,root
beforeEach(()=>{host=document.createElement('div');document.body.append(host);root=createRoot(host);useStore.setState({S:{workouts:[]},user:{id:'one'}})})
afterEach(()=>{act(()=>root.unmount());host.remove();vi.unstubAllGlobals();vi.restoreAllMocks()})
const render=async element=>{await act(async()=>root.render(element))}
const click=async text=>{await act(async()=>[...host.querySelectorAll('button')].find(b=>b.textContent===text).click())}
it('uses Monday week, excludes future/invalid and duplicate workouts without inventing calories',()=>{
 const w=(id,d,calories)=>({id,d,start:100,end:60100,garminActivity:{calories}})
 const result=weeklyProgress([w('old','2026-10-18',90),w('a','2026-10-19',120),w('a','2026-10-19',120),w('b','2026-10-24',undefined),w('future','2026-10-25',999)],new Date('2026-10-24T12:00:00'))
 expect(result).toMatchObject({first:'2026-10-19',workouts:2,minutes:2,calories:120,calorieCount:1,durationCount:2})
 expect(validGoals({workouts:3,minutes:150,calories:1000})).not.toBeNull();expect(validGoals({workouts:1.5,minutes:1,calories:1})).toBeNull();expect(validGoals({workouts:1,minutes:-1,calories:1})).toBeNull()
})
it('saves only personal goals and cancels unsaved changes',async()=>{
 const S={workouts:[{id:'kept'}],routines:[{id:'plan'}],auroraWeeklyGoals:{workouts:3,minutes:150,calories:1000}};useStore.setState({S});await render(<WeeklyGoals S={S}/>);await click('Editar metas')
 host.querySelector('[name=workouts]').value='4';await act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
 expect(useStore.getState().S.auroraWeeklyGoals.workouts).toBe(4);expect(useStore.getState().S.workouts).toEqual(S.workouts);expect(useStore.getState().S.routines).toEqual(S.routines)
 await click('Editar metas');host.querySelector('[name=workouts]').value='8';await click('Cancelar');expect(useStore.getState().S.auroraWeeklyGoals.workouts).toBe(4)
})
it('native merge keeps goals alongside a concurrent Garmin workout',()=>{
 const base={_ts:1,workouts:[],routines:[],bodyweight:[],customEx:[]};const a=structuredClone(base),b=structuredClone(base)
 a.auroraWeeklyGoals={workouts:3,minutes:150,calories:1000};a._ts=stampChange(base,a,20);b.workouts=[{id:'garmin'}];b._ts=stampChange(base,b,30)
 expect(mergeStates(a,b)).toMatchObject({auroraWeeklyGoals:a.auroraWeeklyGoals,workouts:b.workouts})
})
it('displays Garmin result and posts sync using same-origin session without secrets',async()=>{
 const fetcher=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({connected:true,auto:{enabled:true,last_run:'2026-10-24T12:00:00Z',last_added:1,last_skipped:4,next_run:1792846800}})}).mockResolvedValueOnce({ok:true,json:async()=>({ok:true})});vi.stubGlobal('fetch',fetcher)
 await render(<GarminSummary/>);expect(host.textContent).toContain('1 importado(s) · 4 já existente(s)');await click('Sincronizar agora')
 expect(fetcher.mock.calls[1]).toEqual(['/garmin/sync',expect.objectContaining({method:'POST',credentials:'same-origin',body:'{}'})]);expect(host.textContent).toContain('Consulta em andamento')
})
it('shows auth failures and disables sync when no authorization is available',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:401}));await render(<GarminSummary/>);expect(host.querySelector('[role=alert]').textContent).toContain('Entre no perfil');expect(host.querySelector('button').disabled).toBe(true)
})
it('shows safe server errors without claiming synchronization succeeded',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({connected:true,auto:{enabled:true,last_status:'error',last_error:'Falha Garmin'}})}).mockResolvedValueOnce({ok:false,json:async()=>({error:'Aguarde a operação atual.'})}));await render(<GarminSummary/>);await click('Sincronizar agora');expect(host.textContent).toContain('Falha Garmin');expect(host.textContent).toContain('Aguarde a operação atual.')
})
