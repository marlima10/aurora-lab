import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
let module;
const source=fs.readFileSync(process.argv[2]+'/docker/server/mirror/MMM-Aurora/MMM-Aurora.js','utf8');
vm.runInNewContext(source,{Module:{register:(name,body)=>{module=body}}});
const date=(year,month,day)=>new Date(year,month-1,day);
for(const [value,cells] of [[date(2026,8,15),42],[date(2028,2,29),35],[date(2027,2,1),35]]){
 const result=module.calendarRange(value,'month');assert.equal(result.count,cells);assert.equal(result.start.getDay(),0);
}
const week=module.calendarRange(date(2027,1,1),'week');assert.equal(week.count,7);assert.equal(week.weeks,1);assert.equal(week.start.getFullYear(),2026);assert.equal(week.start.getMonth(),11);assert.equal(week.start.getDate(),27);
const ctx={month:date(2027,1,1),calendarView:'week',calendar(){}};
module.shiftCalendar.call(ctx,1);assert.equal(ctx.month.getDate(),8);
module.shiftCalendar.call(ctx,-1);assert.equal(ctx.month.getDate(),1);
assert(!source.includes('geolocation'));assert(!source.includes('navigator.permissions'));
assert(source.includes('aria-label="Abrir Jarvis"'));assert(source.includes('class="jarvis-icon"'));
const items=[{id:'m',source:'meals',day:'2026-11-27',time:''},{id:'t',source:'training',day:'2026-11-27',time:''},{id:'h',source:'holidays',day:'2026-11-27',time:''},{id:'r',source:'reminders',day:'2026-11-27',time:'09:00'},{id:'p',source:'personal',day:'2026-11-27',time:'14:30'},{id:'x',source:'personal',day:'2026-11-28',time:''}];
assert.deepEqual(module.dayRows(items,'2026-11-27').map(x=>x.id),['r','p','m','t']);assert.equal(module.dayRows(undefined,'2026-11-27').length,0);
console.log('Agenda cells keep personal commitments ahead of imported plans and leave holidays apart.');
console.log('Month/week ranges, leap years, year boundary, navigation, no GPS and named Jarvis shortcut passed.');
