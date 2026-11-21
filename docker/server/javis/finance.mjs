// Read-only queries using the official Actual SDK; no transaction/import API is called.
import http from 'node:http';
import fs from 'node:fs';
import crypto from 'node:crypto';
import * as sdk from '@actual-app/api';
console.log=console.warn=console.debug=console.error=()=>{};
let busy=false;
const fail=(code,message)=>{throw Object.assign(new Error(message),{code})};
const send=(res,status,body)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(body))};
const date=value=>{if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)||new Date(value).toISOString().slice(0,10)!==value)fail(400,'Data inválida.');return value};

export async function query(config,body){
 const {tool,identity,args={}}=body;
 if(!config.ready||!Object.hasOwn(config.identities,identity))fail(403,'Perfil financeiro não autorizado.');
 if(!['aurora_finance_accounts','aurora_finance_summary'].includes(tool))fail(403,'Somente consultas financeiras são permitidas.');
 if(Object.keys(args).some(k=>!['start','end'].includes(k)))fail(400,'Campos não permitidos.');
 const auth=await fetch('http://actual:5006/account/login',{method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),headers:{'Content-Type':'application/json','X-Actual-Password':config.secret},body:JSON.stringify({loginMethod:'header'})});
 const session=await auth.json();if(!auth.ok||!session.data?.token)fail(503,'Actual indisponível.');
 const folder='/data/'+crypto.createHash('sha256').update(identity).digest('hex');fs.mkdirSync(folder,{recursive:true,mode:0o700});
 await sdk.init({dataDir:folder,serverURL:'http://actual:5006',sessionToken:session.data.token,verbose:false});
 try{
  const all=await sdk.getBudgets(),remote=all.filter(b=>b.state==='remote'),wanted=config.budgets?.[identity];
  const budget=wanted?all.find(b=>[b.groupId,b.cloudFileId,b.id].includes(wanted)):remote.length===1?remote[0]:null;
  if(!budget)fail(409,'Selecione o orçamento na configuração privada do conector.');
  await sdk.downloadBudget(budget.groupId||budget.id,config.encryptionPasswords?.[identity]?{password:config.encryptionPasswords[identity]}:undefined);await sdk.sync();
  const accounts=await sdk.getAccounts(),categories=await sdk.getCategories();
  if(tool==='aurora_finance_accounts')return {source:'Actual Budget',accounts:accounts.filter(x=>!x.closed).map(({id,name})=>({id,name})),categories:categories.filter(x=>!x.hidden).map(({id,name})=>({id,name}))};
  const start=date(args.start),end=date(args.end);if(end<start||(Date.parse(end)-Date.parse(start))>366*86400000)fail(400,'Selecione até um ano.');
  let incomeCents=0,expenseCents=0,count=0;
  for(const account of accounts)for(const row of await sdk.getTransactions(account.id,start,end)){
   if(row.is_parent||row.transfer_id||!Number.isSafeInteger(row.amount))continue;
   count++;if(row.amount>=0)incomeCents+=row.amount;else expenseCents-=row.amount;
  }
  return {source:'Actual Budget',start,end,count,incomeCents,expenseCents,periodBalanceCents:incomeCents-expenseCents,note:'Centavos na moeda do orçamento. Transferências excluídas. Contas encerradas incluídas no histórico.'};
 }finally{await sdk.shutdown()}
}

if(!process.env.AURORA_FINANCE_FIXTURE)http.createServer(async(req,res)=>{
 if(req.method==='GET'&&req.url==='/health')return send(res,200,{status:'ok'});
 if(req.method!=='POST'||req.url!=='/query')return send(res,404,{error:'Consulta não disponível.'});
 const config=JSON.parse(fs.readFileSync('/run/secrets/config.json','utf8')),a=Buffer.from(req.headers.authorization||''),b=Buffer.from('Bearer '+config.token);
 if(a.length!==b.length||!crypto.timingSafeEqual(a,b))return send(res,403,{error:'Acesso não autorizado.'});
 if(busy)return send(res,429,{error:'Conector ocupado.'});busy=true;
 try{let size=0,chunks=[];for await(const chunk of req){size+=chunk.length;if(size>16384)fail(413,'Pedido acima do limite.');chunks.push(chunk)};send(res,200,await query(config,JSON.parse(Buffer.concat(chunks).toString('utf8'))))}
 catch(e){send(res,e.code||503,{error:e.code?e.message:'Não foi possível consultar o Actual.'})}finally{busy=false}
}).listen(8000,'0.0.0.0');
