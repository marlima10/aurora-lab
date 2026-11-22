-- Upstream 0_init omits this field from the pinned Prisma schema.
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS "onboardingPreferences" JSONB;
