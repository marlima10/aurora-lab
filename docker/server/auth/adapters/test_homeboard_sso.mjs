import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { auroraEditor } from './aurora-auth.mjs';
const secret = 'fixture-private-proxy-secret-000000000';
const request = (role, key=secret) => ({headers:{'x-aurora-identity':role,'x-aurora-proxy-secret':key}});
test('existing editor can edit without changing native data',()=>assert.equal(auroraEditor(request('editor'),secret),true));
test('viewer, missing and forged identity cannot edit',()=>{
  for(const req of [request('viewer'),request('root'),request('editor','wrong'),{headers:{}}])assert.equal(auroraEditor(req,secret),false);
});
test('missing private secret fails closed',()=>assert.throws(()=>auroraEditor(request('editor'),'')));
