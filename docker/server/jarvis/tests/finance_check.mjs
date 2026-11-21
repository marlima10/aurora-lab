import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';

let imports=[],budgets=[{state:'remote',groupId:'fixture-sync'}],syncs=0,checks=0;
const sdk={
 init:async config=>{assert.equal(config.sessionToken,'fixture-token')},
 shutdown:async()=>{},sync:async()=>{syncs++},
 getBudgets:async()=>budgets,
 downloadBudget:async id=>assert.equal(id,'fixture-sync'),
 getAccounts:async()=>[{id:'fixture-account',name:'Conta fictícia'},{id:'fixture-closed',name:'Conta encerrada',closed:true}],
 getCategories:async()=>[{id:'fixture-category',name:'Categoria fictícia'}],
 getTransactions:async id=>id==='fixture-closed'?[{amount:-1000}]:[{amount:1000},{amount:-250},{amount:-900,transfer_id:'fixture-transfer'},{amount:-50,is_parent:true}],
 importTransactions:async(account,rows,opts)=>{imports.push({account,rows,opts});return {added:['fixture-transaction'],updated:[],errors:[]}}
};
const quiet={log(){},debug(){},warn(){}};
const context=vm.createContext({console:quiet,Buffer,AbortSignal,fetch:async(url,options)=>{
 assert.equal(url,'http://actual:5006/account/login');assert.equal(options.headers['X-Actual-Password'],'fixture-secret');return {ok:true,json:async()=>({data:{token:'fixture-token'}})}
}});
const source=fs.readFileSync(new URL('../finance.mjs',import.meta.url),'utf8')+'\nexport {execute};';
const modules={
 'node:http':{default:{createServer:()=>({listen(){}})}},
 'node:fs':{default:{mkdirSync(){},readFileSync(){return '{}'}}},
 'node:crypto':{default:crypto},'@actual-app/api':sdk
};
const module=new vm.SourceTextModule(source,{context});
await module.link(async name=>{
 const values=modules[name];assert.ok(values,'unexpected import '+name);
 const synthetic=new vm.SyntheticModule(Object.keys(values),function(){for(const [k,v]of Object.entries(values))this.setExport(k,v)},{context});return synthetic;
});
await module.evaluate();
const execute=module.namespace.execute;
const cfg={ready:true,identities:{fixture:'mapped'},secret:'fixture-secret'};
const base={identity:'fixture',args:{}};
await assert.rejects(()=>execute(cfg,{...base,identity:'other',tool:'finance_accounts'}),/Perfil/);checks++;
const summary=await execute(cfg,{...base,tool:'finance_summary',args:{start:'2026-11-01',end:'2026-11-21'}});
assert.equal(summary.incomeCents,1000);assert.equal(summary.expenseCents,1250);assert.equal(summary.balanceCents,-250);checks++;
const transaction={accountId:'fixture-account',date:'2026-11-21',amount:-8500,payee:'Mercado fictício',categoryId:'fixture-category'};
await assert.rejects(()=>execute(cfg,{...base,tool:'finance_add_transaction',args:transaction}),/Confirmação/);assert.equal(imports.length,0);checks++;
await assert.rejects(()=>execute(cfg,{...base,tool:'finance_add_transaction',operation_id:'fixture-confirmation-00001',args:{...transaction,amount:8.5}}),/centavos/);assert.equal(imports.length,0);checks++;
const preview=await execute(cfg,{...base,tool:'finance_add_transaction',validate_only:true,args:transaction});assert.equal(preview.preview.account,'Conta fictícia');assert.equal(imports.length,0);checks++;
await execute(cfg,{...base,tool:'finance_add_transaction',operation_id:'fixture-confirmation-00001',args:transaction});
assert.equal(imports[0].rows[0].imported_id,'aurora-jarvis-fixture-confirmation-00001');assert.equal(imports[0].rows[0].amount,-8500);assert.equal(imports[0].opts.reimportDeleted,false);assert.equal(imports[0].rows[0].cleared,false);checks++;
budgets=[...budgets,{state:'remote',groupId:'other'}];
await assert.rejects(()=>execute(cfg,{...base,tool:'finance_accounts'}),/Escolha o orçamento/);checks++;
assert.ok(syncs>0);console.log(checks+' finance checks passed with a synthetic SDK; no real budget accessed.');
