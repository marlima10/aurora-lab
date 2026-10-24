import { timingSafeEqual } from 'node:crypto';
export const ssoEnabled=()=>process.env.AURORA_SSO_ENABLED==='1';
export function auroraEditor(req,secret=process.env.AURORA_SSO_SECRET){
  if(!secret||secret.length<32)throw Error('Configure private SSO secret');
  const supplied=req.headers['x-aurora-proxy-secret'];
  if(typeof supplied!=='string')return false;
  const a=Buffer.from(supplied),b=Buffer.from(secret);
  return a.length===b.length&&timingSafeEqual(a,b)&&req.headers['x-aurora-identity']==='editor';
}
