import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import { auroraSession, auroraPairingProof } from './aurora-sso.js';
const secret='fixture-not-a-production-secret-000000';
const users=[{id:'existing-profile',role:'user',workouts:['untouched']},{id:'disabled-profile',disabled:true}];
const request=(id,key=secret)=>({headers:{'x-aurora-identity':id,'x-aurora-proxy-secret':key}});
test('maps only an existing profile, preserving its data and permissions',()=>{
  const snapshot=JSON.stringify(users),session=auroraSession(request('existing-profile'),users,secret,1000);
  assert.equal(session.user,users[0]);assert.equal(session.user.role,'user');assert.equal(session.exp,61000);assert.equal(session.bearer,false);assert.equal(JSON.stringify(users),snapshot);
});
test('rejects missing, forged, disabled or nonexistent identities',()=>{
  for(const req of [{headers:{}},request('existing-profile','attacker'),request('existing-profile','a'.repeat(secret.length)),request('disabled-profile'),request('other')])assert.equal(auroraSession(req,users,secret),null);
});
test('refuses missing private proxy secret',()=>assert.throws(()=>auroraSession(request('existing-profile'),users,'')));

test('central identity confirms Garmin pairing only, never native account changes',()=>{
  assert.equal(auroraPairingProof(request('existing-profile'),users[0],users,'pair',secret),true);
  for(const action of ['password','email','passkey-add','passkey-remove','device-link','account-delete']) assert.equal(auroraPairingProof(request('existing-profile'),users[0],users,action,secret),false);
  assert.equal(auroraPairingProof(request('existing-profile','forged'),users[0],users,'pair',secret),false);
  assert.equal(auroraPairingProof(request('existing-profile'),users[1],users,'pair',secret),false);
});
