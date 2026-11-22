import assert from 'node:assert/strict';
import {nativeSet} from './convert.mjs';
let v=nativeSet({min:1.5,done:true},0,'kg');assert.deepEqual(v.types,['TIME']);assert.equal(v.valuesSec[0],90);assert(v.completed);
v=nativeSet({w:20,r:12,done:false},1,'kg');assert.deepEqual(v.types,['WEIGHT','REPS']);assert.deepEqual(v.valuesInt,[20,12]);assert.equal(v.completed,false);
assert.throws(()=>nativeSet({w:2.5},0,'kg'),/Fractional/);
assert.equal(nativeSet({},0,'kg').type,'NA');
assert.equal(nativeSet({r:8},0,'lbs').units[0],'lbs');
console.log('Time, weight, reps, completion, units and rejection of lossy rounding passed.');
