import { timingSafeEqual } from 'node:crypto';

export function auroraSession(req, users, secret=process.env.AURORA_SSO_SECRET, now=Date.now()) {
  if (!secret || secret.length<32) throw Error('Configure AURORA_SSO_SECRET before enabling SSO');
  const supplied=req.headers['x-aurora-proxy-secret'];
  if (typeof supplied!=='string') return null;
  const a=Buffer.from(supplied),b=Buffer.from(secret);
  if (a.length!==b.length || !timingSafeEqual(a,b)) return null;
  const id=req.headers['x-aurora-identity'];
  if (typeof id!=='string') return null;
  const user=users.find(u=>u.id===id&&!u.disabled);
  return user?{user,exp:now+60000,bearer:false}:null;
}
