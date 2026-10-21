import test from 'node:test';
import assert from 'node:assert/strict';
import { trainingMetrics, workoutMinutes } from './frontend/src/lib/training-metrics.js';
const now = new Date('2026-10-21T12:00:00');
const w = (id, d, calories, min=60) => ({id,d,start:1,end:1+min*60000,garminActivity:{calories}});
test('daily sums, ordering and no duplicate workout',()=>{
 const a=w('a','2026-10-20',300),b=w('b','2026-10-20',250,30),c=w('c','2026-10-21',0);
 const r=trainingMetrics([c,a,b,a],7,now);
 assert.deepEqual(r.minutes.map(p=>p.y),[90,60]);assert.deepEqual(r.calories.map(p=>p.y),[550,0]);assert.equal(r.workoutsCount,3);
});
test('missing, negative and non-finite calories are not zero',()=>{
 const r=trainingMetrics([w('a','2026-10-20',null),w('b','2026-10-20',-1),w('c','2026-10-20',NaN),w('d','2026-10-20',true)],30,now);
 assert.equal(r.calories.length,0);assert.equal(r.calorieCount,0);assert.equal(r.workoutsCount,4);
});
test('local date filter includes first day and excludes future/invalid',()=>{
 const rows=[w('a','2026-10-15',10),w('b','2026-10-14',20),w('c','2026-10-22',30),w('d','2026-02-30',40)];
 assert.equal(trainingMetrics(rows,7,now).workoutsCount,1);assert.equal(trainingMetrics(rows,0,now).workoutsCount,2);
});
test('time is session duration once, with completed timed sets fallback',()=>{
 assert.equal(workoutMinutes({...w('a','2026-10-20',1),entries:[{mode:'cardio',sets:[{min:20,done:true}]}]}),60);
 assert.equal(workoutMinutes({entries:[{mode:'cardio',sets:[{min:20,done:true},{min:50,done:false}]},{mode:'time',sets:[{sec:60,done:true}]}]}),21);
 assert.equal(workoutMinutes({}),null);
});
test('empty state, partial coverage and stable input',()=>{
 const row=w('a','2026-10-20',123);const before=JSON.stringify(row);
 assert.equal(trainingMetrics([],30,now).workoutsCount,0);trainingMetrics([row],30,now);assert.equal(JSON.stringify(row),before);
 const result=trainingMetrics([row,w('b','2026-10-20',undefined)],30,now);assert.equal(result.calorieCount,1);assert.equal(result.workoutsCount,2);
});
