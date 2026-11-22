import fs from 'node:fs';
function change(path,from,to){let s=fs.readFileSync(path,'utf8');if(!s.includes(from))throw Error('Upstream changed: '+path);fs.writeFileSync(path,s.replace(from,to))}
fs.copyFileSync('aurora/aurora-sso.ts','src/shared/lib/aurora-sso.ts');
change('src/features/auth/lib/better-auth.ts','export const auth = betterAuth({','import { isAuroraSsoRequest } from "@/shared/lib/aurora-sso";\n\nexport const auth = betterAuth({');
change('src/features/auth/lib/better-auth.ts','trustedOrigins: ["*", "workoutcool://", "expo://"]','trustedOrigins: [env.BETTER_AUTH_URL]');
change('src/features/auth/lib/better-auth.ts','enabled: true,\n      clientId:', 'enabled: process.env.AURORA_LAB_SSO !== "1",\n      clientId:');
change('src/features/auth/lib/better-auth.ts','    enabled: true,\n  },\n  socialProviders:', '    enabled: process.env.AURORA_LAB_SSO !== "1",\n  },\n  socialProviders:');
fs.appendFileSync('src/features/auth/lib/better-auth.ts',`
export async function auroraLabSession(headers: Headers) {
  if (!isAuroraSsoRequest(headers)) return null;
  const user = await prisma.user.findUnique({ where: { id: process.env.AURORA_LAB_USER_ID || "aurora-rafael-lab" }, include: { accounts: { select: { providerId: true } } } });
  if (!user || user.banned) return null;
  return { user, session: { id: "aurora-lab", token: "delegated-sso-no-native-token", userId: user.id, expiresAt: new Date(Date.now()+3600000), createdAt: new Date(), updatedAt: new Date(), ipAddress: null, userAgent: null, impersonatedBy: null } };
}
const originalGetSession = auth.api.getSession.bind(auth.api);
auth.api.getSession = (async (options: {headers: Headers}) => process.env.AURORA_LAB_SSO === "1" ? auroraLabSession(new Headers(options.headers)) : originalGetSession(options as never)) as typeof auth.api.getSession;
`);
fs.writeFileSync('app/api/auth/[...all]/route.ts',`import { NextRequest, NextResponse } from "next/server";
import { auroraLabSession } from "@/features/auth/lib/better-auth";
export async function GET(request: NextRequest) {
 if (request.nextUrl.pathname.endsWith("/get-session")) return NextResponse.json(await auroraLabSession(request.headers),{headers:{"Cache-Control":"no-store"}});
 return NextResponse.json({error:"Use o login AuroraLAB."},{status:403});
}
export async function POST() {return NextResponse.json({error:"Use o login AuroraLAB."},{status:403});}
`);
change('proxy.ts','import { getSessionCookie }','import { isAuroraSsoRequest } from "@/shared/lib/aurora-sso";\nimport { getSessionCookie }');
change('proxy.ts','if (!session) {','if (!session && !isAuroraSsoRequest(request.headers)) {');
change('src/shared/api/mobile-auth.ts','const rawCookieHeader = req.headers.get("cookie");','const rawCookieHeader = req.headers.get("cookie") || "";');
change('src/shared/api/mobile-auth.ts','if (!rawCookieHeader) {','if (!rawCookieHeader && !req.headers.get("x-aurora-lab-secret")) {');
fs.writeFileSync('src/shared/lib/analytics/server.ts',`export const setupAnalytics = async (_options?: unknown) => ({track: (_event: unknown) => {}});\n`);
fs.writeFileSync('src/shared/lib/analytics/client.tsx',`export const AnalyticsProvider = () => null;\nexport const track = (_options: unknown) => {};\n`);
fs.writeFileSync('src/shared/lib/analytics/proxy.ts',`export function trackFromProxy(_options: unknown) {}\n`);
change('next.config.ts','reactStrictMode: true,','reactStrictMode: true,\n  experimental: { cpus: 2 },');
change('app/[locale]/layout.tsx','<AdScripts />','<div style={{background:"#8a420a",color:"white",padding:"10px",textAlign:"center",fontSize:"14px"}}>AMBIENTE DE TESTE · cópia do openGym · alterações não voltam ao aplicativo atual. <a href="/pt/aurora-import" style={{textDecoration:"underline"}}>Dados importados</a> · <a href="https://auroraserver.tail7d26f7.ts.net/mirror/" style={{textDecoration:"underline"}}>AuroraLAB</a></div>');
// No build-time DB queries; all personal data arrives only after the image has been built.
fs.appendFileSync('app/[locale]/layout.tsx','\nexport const dynamic = "force-dynamic";\n');
fs.mkdirSync('app/[locale]/(app)/aurora-import',{recursive:true});fs.copyFileSync('aurora/lab-page.tsx','app/[locale]/(app)/aurora-import/page.tsx');
for(const path of ['src/features/auth/lib/better-auth.ts','app/api/workout-sessions/sync/route.ts']){
 const s=fs.readFileSync(path,'utf8');fs.writeFileSync(path,s.split('\n').filter(line=>!line.trim().startsWith('console.log(')).join('\n'));
}

fs.writeFileSync('app/api/billing/status/route.ts',`import {NextRequest,NextResponse} from "next/server";
import {auroraLabSession} from "@/features/auth/lib/better-auth";
export async function GET(request:NextRequest){if(!await auroraLabSession(request.headers))return NextResponse.json({error:"Unauthorized"},{status:401});return NextResponse.json({isPremium:false,canUpgrade:false,billingDisabled:true});}
`);
