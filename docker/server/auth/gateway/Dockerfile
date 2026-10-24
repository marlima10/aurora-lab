FROM nginx:stable-alpine@sha256:970364228b1e4f932abc22d321932816782cca8a20b85a77552a7cfe9acfb3b5
RUN addgroup -g 64024 aurora-sso \
 && sed -i 's/^user .*/user nginx aurora-sso;/' /etc/nginx/nginx.conf \
 && sed -i 's/worker_processes .*/worker_processes 2;/' /etc/nginx/nginx.conf
