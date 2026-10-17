FROM php:8.2-fpm-alpine
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS sqlite-dev \
    && docker-php-ext-install pdo_sqlite \
    && apk del .build-deps \
    && apk add --no-cache sqlite-libs
COPY php-entrypoint.sh /usr/local/bin/aurora-php-entrypoint
RUN chmod 0755 /usr/local/bin/aurora-php-entrypoint
ENTRYPOINT ["/usr/local/bin/aurora-php-entrypoint"]