// @vitest-environment happy-dom
import React, {act} from 'react'
import {createRoot} from 'react-dom/client'
import {afterEach, beforeEach, expect, it, vi} from 'vitest'
import {useStore} from '../store/useStore.js'
import Home from '../views/Home.jsx'
import Stats from '../views/Stats.jsx'
import TrainingMetrics from './TrainingMetrics.jsx'
vi.mock('react-router-dom',()=>({useNavigate:()=>()=>{}}))
globalThis.IS_REACT_ACT_ENVIRONMENT=true
let host,root
beforeEach(()=>{host=document.createElement('div');document.body.append(host);root=createRoot(host)})
afterEach(()=>{act(()=>root.unmount());host.remove()})
const today=()=>new Date().toLocaleDateString('sv-SE')
const workout=(id,calories,d=today())=>({id,d,start:1,end:3600001,entries:[],garminActivity:{calories}})
for(const [name,View] of [['home',Home],['stats',Stats]]) it(name+' renders progress, time and calories from current profile',()=>{
 useStore.setState(s=>({S:{...s.S,routines:[],workouts:[workout('one',450)],bodyweight:[],dayPlan:{},week:{},active:null},user:null}))
 act(()=>root.render(<View/>))
 expect(host.textContent).toContain('Exercise progress');expect(host.textContent).toContain('Tempo de exercício');expect(host.textContent).toContain('Calorias gastas')
 expect(host.querySelector('[aria-label="Tempo de exercício"]').textContent).toContain('60');expect(host.querySelector('[aria-label="Calorias gastas"]').textContent).toContain('450')
 expect(host.querySelectorAll('section[aria-label="Gráficos de treino"]')).toHaveLength(1)
})
it('shows real zero, missing coverage and daily accessible table',()=>{
 act(()=>root.render(<TrainingMetrics S={{workouts:[workout('one',0),workout('two',null)]}}/>))
 const card=host.querySelector('[aria-label="Calorias gastas"]');expect(card.textContent).toContain('1 de 2 treinos');expect(card.querySelector('tbody tr').textContent).toContain('0')
})
it('empty calories are unavailable instead of zero and range excludes older workouts',()=>{
 const old=new Date();old.setDate(old.getDate()-20)
 act(()=>root.render(<TrainingMetrics S={{workouts:[workout('old',500,old.toLocaleDateString('sv-SE')),workout('now',null)]}}/>))
 act(()=>[...host.querySelectorAll('button')].find(b=>b.textContent==='7 dias').click())
 const card=host.querySelector('[aria-label="Calorias gastas"]');expect(card.textContent).toContain('Sem calorias informadas');expect(card.textContent).toContain('0 de 1 treinos');expect(card.querySelector('svg')).toBeNull()
})
