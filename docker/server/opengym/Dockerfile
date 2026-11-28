FROM node:26-alpine@sha256:6bd9ab43c0ec0190ca7b2d193906cb8b7edf6e7f4afa43ddeccd6452710bffb5 AS build
RUN apk add --no-cache git
WORKDIR /upstream
# Exact upstream 1.4.5 source, sparse checkout avoids exercise videos already in the runtime image.
RUN git init . && git remote add origin https://github.com/DuarteSantos8/openGym.git \
 && git config core.sparseCheckout true \
 && printf 'frontend/\napi/coach/core/\nLICENSE\nNOTICE.md\n' > .git/info/sparse-checkout \
 && git -c protocol.version=2 fetch --depth=1 --filter=blob:none origin 2d70e026effc6602f513555166a97443520f0572 \
 && git checkout --detach FETCH_HEAD \
 && test "$(git rev-parse HEAD)" = 2d70e026effc6602f513555166a97443520f0572
WORKDIR /upstream/frontend
RUN npm ci --ignore-scripts --no-audit --no-fund
WORKDIR /upstream
COPY charts.patch /tmp/charts.patch
RUN git apply --check /tmp/charts.patch && git apply /tmp/charts.patch
COPY frontend/ /upstream/frontend/
WORKDIR /upstream/frontend
# Vite stamps the service worker from the content hash, so installed PWAs update too.
RUN APP_BUILD=auroralab-53 npm run build

FROM ghcr.io/duartesantos8/opengym-web:1.4.5@sha256:e621677554302a0e1745e3b8c90acddc7d7149e118c4d683d51c13aa88f47d27
COPY --from=build /upstream/frontend/dist/ /usr/share/nginx/html/
COPY --from=build /upstream/LICENSE /upstream/NOTICE.md /usr/share/nginx/html/aurora-source/
COPY charts.patch /usr/share/nginx/html/aurora-source/charts.patch
LABEL org.opencontainers.image.source="https://github.com/marlima10/aurora-lab" \
 org.opencontainers.image.version="1.4.5+auroralab-53"
