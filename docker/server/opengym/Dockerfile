FROM node:22-alpine AS build
RUN apk add --no-cache git
WORKDIR /upstream
# Exact upstream 1.4.1 source, sparse checkout avoids exercise videos already in the runtime image.
RUN git init . && git remote add origin https://github.com/DuarteSantos8/openGym.git \
 && git config core.sparseCheckout true \
 && printf 'frontend/\napi/coach/core/\nLICENSE\nNOTICE.md\n' > .git/info/sparse-checkout \
 && git -c protocol.version=2 fetch --depth=1 --filter=blob:none origin 464355ef43d4c8f8a4e0bb6db9c2af7f240593b5 \
 && git checkout --detach FETCH_HEAD \
 && test "$(git rev-parse HEAD)" = 464355ef43d4c8f8a4e0bb6db9c2af7f240593b5
COPY charts.patch /tmp/charts.patch
RUN git apply --check /tmp/charts.patch && git apply /tmp/charts.patch
COPY frontend/ /upstream/frontend/
WORKDIR /upstream/frontend
RUN npm ci --ignore-scripts --no-audit --no-fund
# Vite stamps the service worker from the content hash, so installed PWAs update too.
RUN APP_BUILD=auroralab-19 npm run build

FROM ghcr.io/duartesantos8/opengym-web:1.4.1@sha256:e32cae9d2f4aad0c5e1b7888c9bfc712b2306ddfe3c65bc4cfefd4b0002e86d3
COPY --from=build /upstream/frontend/dist/ /usr/share/nginx/html/
COPY --from=build /upstream/LICENSE /upstream/NOTICE.md /usr/share/nginx/html/aurora-source/
COPY charts.patch /usr/share/nginx/html/aurora-source/charts.patch
LABEL org.opencontainers.image.source="https://github.com/marlima10/aurora-lab" \
 org.opencontainers.image.version="1.4.1+auroralab-19"
