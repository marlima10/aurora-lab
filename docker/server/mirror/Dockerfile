FROM node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54
ARG MM_COMMIT=f138f5b690ceab6450f55c852ac81d268363f563
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/magicmirror
RUN curl -fsSL https://codeload.github.com/MagicMirrorOrg/MagicMirror/tar.gz/${MM_COMMIT} | tar xz --strip-components=1 && npm ci --omit=dev --omit=optional --ignore-scripts --no-audit --no-fund && npm cache clean --force
COPY config.js config/config.js
COPY custom.css config/custom.css
COPY install.mjs ./aurora-install.mjs
RUN node aurora-install.mjs && rm -f js/positions.js && ln -s /tmp/aurora-positions.js js/positions.js && ln -s /tmp/aurora-basepath.js config/basepath.js
COPY MMM-Aurora ./modules/MMM-Aurora
USER node
EXPOSE 8080
CMD ["node", "serveronly"]
