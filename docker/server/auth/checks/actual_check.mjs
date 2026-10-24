import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {patchActual,ORIGINAL,REPLACEMENT} from '../adapters/actual-login.mjs';
const fixture=Buffer.from('const availableLoginMethods = listLoginMethods(); const methods = listLoginMethods(); const data={loginMethod: '+ORIGINAL+',availableLoginMethods,methods};');
const digest=createHash('sha256').update(fixture).digest('hex');
assert.throws(()=>patchActual(fixture),/reviewed revision/);
assert.throws(()=>patchActual(Buffer.from('unexpected'),createHash('sha256').update('unexpected').digest('hex')),/contract/);
const result=patchActual(fixture,digest)+'data';
for(const [method,rows] of [['header',[{method:'password',active:1}]],['password',[{method:'password',active:1}]],['openid',[{method:'password'},{method:'openid',active:1}]]]){
 const data=vm.runInNewContext(result,{getLoginMethod:()=>method,listLoginMethods:()=>rows});
 assert.equal(data.loginMethod,method);
 assert.equal(data.availableLoginMethods.find(r=>r.active).method,method);
 assert.equal(data.methods.find(r=>r.active).method,method);
}
console.log('5 Actual checks passed: reviewed source, contract and native method selection.');
