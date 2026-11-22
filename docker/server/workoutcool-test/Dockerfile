FROM node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee AS builder
ARG UPSTREAM_COMMIT=d52f9f62d2a5fcbb78d67a95dc8763f9a34dbf9e
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl openssl && rm -rf /var/lib/apt/lists/* && corepack enable && corepack prepare pnpm@10.6.2 --activate
WORKDIR /app
RUN curl -fsSL https://codeload.github.com/Snouzy/workout-cool/tar.gz/${UPSTREAM_COMMIT} | tar xz --strip-components=1
RUN pnpm install --frozen-lockfile
COPY patch.mjs aurora-sso.ts lab-page.tsx ./aurora/
RUN node aurora/patch.mjs
ENV NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production NODE_OPTIONS=--max-old-space-size=3072
ENV DATABASE_URL=postgresql://build:build@127.0.0.1:9/build BETTER_AUTH_SECRET=build-only-placeholder-not-a-runtime-secret GOOGLE_CLIENT_ID=disabled GOOGLE_CLIENT_SECRET=disabled DEFAULT_BILLING_MODE=DISABLED NEXT_PUBLIC_SHOW_ADS=false REVENUECAT_SECRET_KEY=disabled-local-evaluation STRIPE_SECRET_KEY=sk_test_disabled_local_evaluation
ENV BETTER_AUTH_URL=https://auroraserver.tail7d26f7.ts.net:8444 NEXT_PUBLIC_APP_URL=https://auroraserver.tail7d26f7.ts.net:8444
RUN pnpm exec prisma generate && pnpm build > /tmp/aurora-build.log 2>&1 || (tail -90 /tmp/aurora-build.log; exit 1)
FROM builder AS runner
ENV NODE_OPTIONS=--max-old-space-size=1024 PORT=3000 HOSTNAME=0.0.0.0
COPY entrypoint.sh import.mjs convert.mjs ./aurora/
COPY schema.sql ./prisma/migrations/1_aurora_schema_completion/migration.sql
USER 10001:10001
ENTRYPOINT ["sh","/app/aurora/entrypoint.sh"]
CMD ["node","node_modules/next/dist/bin/next","start","--hostname","0.0.0.0"]
