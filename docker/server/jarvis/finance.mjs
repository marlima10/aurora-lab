// Official Actual client. The SDK owns budget synchronization; no direct SQL writes.
import http from 'node:http';
import fs from 'node:fs';
import crypto from 'node:crypto';
import * as api from '@actual-app/api';

console.log = () => {}; console.debug = () => {}; console.warn = () => {};
let busy = false;
const cfg = () => JSON.parse(fs.readFileSync('/run/secrets/config.json', 'utf8'));
const send = (res, status, body) => { res.writeHead(status, {'Content-Type':'application/json','Cache-Control':'no-store'}); res.end(JSON.stringify(body)); };
function fail(status, message) { throw Object.assign(new Error(message), {status}); }
function date(value) {
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)||new Date(value).toISOString().slice(0,10)!==value)fail(400,'Data inválida.');
  return value;
}

async function execute(c, data) {
  const args=data.args||{}, identity=data.identity;
  if(!c.ready||!Object.hasOwn(c.identities,identity))fail(403,'Perfil financeiro não autorizado.');
  const auth=await fetch('http://actual:5006/account/login', {method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),
    headers:{'Content-Type':'application/json','X-Actual-Password':c.secret},body:JSON.stringify({loginMethod:'header'})});
  const login=await auth.json(), token=login.data?.token;
  if(!auth.ok||typeof token!=='string')fail(503,'Actual não autorizou o conector.');
  const folder='/data/'+crypto.createHash('sha256').update(identity).digest('hex');
  fs.mkdirSync(folder,{recursive:true,mode:0o700});
  await api.init({dataDir:folder,serverURL:'http://actual:5006',sessionToken:token,verbose:false});
  try {
    const budgets=await api.getBudgets();
    const configured=c.budgets?.[identity];
    const remote=budgets.filter(b=>b.state==='remote');
    const selected=configured ? budgets.find(b=>b.groupId===configured||b.cloudFileId===configured||b.id===configured) : remote.length===1 ? remote[0] : null;
    if(!selected)fail(409,'Escolha o orçamento autorizado na configuração privada do conector.');
    const syncId=selected.groupId||selected.id;
    if(!syncId)fail(409,'Identificador de sincronização ausente.');
    await api.downloadBudget(syncId,c.encryptionPasswords?.[identity]?{password:c.encryptionPasswords[identity]}:undefined);
    await api.sync();
    const accounts=await api.getAccounts(), categories=await api.getCategories();
    if(data.tool==='finance_accounts')return {source:'Actual Budget',accounts:accounts.filter(a=>!a.closed).map(a=>({id:a.id,name:a.name})),categories:categories.filter(a=>!a.hidden).map(a=>({id:a.id,name:a.name}))};
    if(data.tool==='finance_summary') {
      const start=date(args.start), end=date(args.end);
      if(end<start||(Date.parse(end)-Date.parse(start))>366*86400000)fail(400,'Selecione até um ano.');
      let income=0,expense=0,count=0;
      for(const account of accounts) {
        for(const row of await api.getTransactions(account.id,start,end)) {
          if(row.is_parent||row.transfer_id)continue;
          if(!Number.isSafeInteger(row.amount))continue;
          count++;if(row.amount>=0)income+=row.amount;else expense+=-row.amount;
        }
      }
      return {source:'Actual Budget',start,end,count,incomeCents:income,expenseCents:expense,balanceCents:income-expense,note:'Transferências excluídas; valores em centavos na moeda do orçamento.'};
    }
    if(data.tool==='finance_add_transaction') {
      if(!accounts.some(a=>a.id===args.accountId&&!a.closed))fail(400,'Conta inválida.');
      if(!Number.isSafeInteger(args.amount)||args.amount===0||Math.abs(args.amount)>100000000)fail(400,'Valor em centavos inválido.');
      if(typeof args.payee!=='string'||!args.payee.trim()||args.payee.length>150)fail(400,'Favorecido inválido.');
      if(args.categoryId&&!categories.some(c=>c.id===args.categoryId&&!c.hidden))fail(400,'Categoria inválida.');
      if(data.validate_only===true)return {preview:{account:accounts.find(a=>a.id===args.accountId).name,category:categories.find(c=>c.id===args.categoryId)?.name||'Sem categoria'}};
      if(typeof data.operation_id!=='string'||!/^[\w-]{20,100}$/.test(data.operation_id))fail(400,'Confirmação necessária.');
      const row={date:date(args.date),amount:args.amount,payee_name:args.payee.trim(),notes:String(args.notes||'').slice(0,1000),imported_id:'aurora-jarvis-'+data.operation_id,cleared:false};
      if(args.categoryId)row.category=args.categoryId;
      const result=await api.importTransactions(args.accountId,[row],{reimportDeleted:false,defaultCleared:false});
      if(result.errors?.length)fail(409,'Actual recusou o lançamento. Confira no aplicativo.');
      await api.sync();
      return {saved:true,source:'Actual Budget',added:result.added?.length||0,updated:result.updated?.length||0};
    }
    fail(404,'Ferramenta financeira não permitida.');
  } finally { await api.shutdown(); }
}

http.createServer(async(req,res)=>{
  if(req.method==='GET'&&req.url==='/health')return send(res,200,{status:'ok'});
  if(req.method!=='POST'||req.url!=='/call')return send(res,404,{error:'Operação não encontrada.'});
  const c=cfg(), supplied=Buffer.from(req.headers.authorization||''), expected=Buffer.from('Bearer '+c.token);
  if(supplied.length!==expected.length||!crypto.timingSafeEqual(supplied,expected))return send(res,403,{error:'Acesso interno não autorizado.'});
  if(busy)return send(res,429,{error:'Conector financeiro ocupado.'});
  busy=true;
  try {
    let size=0,chunks=[];
    for await(const chunk of req){size+=chunk.length;if(size>65536)fail(413,'Pedido acima do limite.');chunks.push(chunk);}
    const data=JSON.parse(Buffer.concat(chunks).toString('utf8'));
    send(res,200,await execute(c,data));
  } catch(error){send(res,error.status||503,{error:error.status?error.message:'Não foi possível concluir no Actual. Confira o aplicativo antes de repetir.'});}
  finally{busy=false;}
}).listen(8000,'0.0.0.0');
