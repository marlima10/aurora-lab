import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root = process.argv[2];
const app = fs.readFileSync(root+'/app.js','utf8');
const recognition = 'function recLangTheoGiaoDien'+app.split('function recLangTheoGiaoDien')[1].split('function rateToPct')[0];
for (const [code, expected] of [['pt','pt-BR'],['en','en-US'],['vi','vi-VN']]) {
  const ctx={window:{JavisI18n:{lang:()=>code}}};vm.createContext(ctx);vm.runInContext(recognition,ctx);
  assert.equal(ctx.recLangTheoGiaoDien(),expected);
}
const dictate=fs.readFileSync(root+'/dictate.js','utf8');
const tag='function langTag'+dictate.split('function langTag')[1].split('function pageHidden')[0];
const ctx={document:{documentElement:{getAttribute:()=> 'pt'}}};vm.createContext(ctx);vm.runInContext(tag,ctx);assert.equal(ctx.langTag(),'pt-BR');
const store=new Map();const prefs={localStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v)}};vm.createContext(prefs);
const migrate=fs.readFileSync(root+'/aurora-locale.js','utf8');vm.runInContext(migrate,prefs);assert.equal(store.get('javis.ui_lang'),'pt');assert.equal(store.get('javis.voice'),'pt-BR-AntonioNeural');assert.equal(store.get('javis.rate'),'0.90');
store.set('javis.ui_lang','en');store.set('javis.voice','pt-BR-FranciscaNeural');store.set('javis.rate','1.10');vm.runInContext(migrate,prefs);assert.equal(store.get('javis.ui_lang'),'en');assert.equal(store.get('javis.voice'),'pt-BR-FranciscaNeural');assert.equal(store.get('javis.rate'),'1.10');
console.log('Recognition pt-BR/en/vi, dictation pt-BR and one-time preference migration passed.');
