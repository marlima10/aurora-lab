import { timingSafeEqual } from "node:crypto";
export function isAuroraSsoRequest(headers: Headers): boolean {
  const secret = process.env.AURORA_LAB_PROXY_SECRET || "";
  const supplied = headers.get("x-aurora-lab-secret") || "";
  const identity = headers.get("x-aurora-identity") || "";
  const a = Buffer.from(supplied);
  const b = Buffer.from(secret);
  return process.env.AURORA_LAB_SSO === "1" && secret.length >= 32 && a.length === b.length
    && timingSafeEqual(a, b) && identity === "aurora@server.local";
}
