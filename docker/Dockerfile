FROM composer:2 AS composer

FROM php:8.2-fpm-alpine
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS sqlite-dev \
    && docker-php-ext-install pdo_sqlite \
    && apk del .build-deps \
    && apk add --no-cache sqlite-libs
COPY --from=composer /usr/bin/composer /usr/local/bin/composer
WORKDIR /var/www/backend
COPY backend/ ./
RUN composer dump-autoload --optimize --no-dev --no-interaction
COPY docker/php-entrypoint.sh /usr/local/bin/aurora-php-entrypoint
RUN sed -i 's/\r$//' /usr/local/bin/aurora-php-entrypoint \
    && chmod 0755 /usr/local/bin/aurora-php-entrypoint
ENTRYPOINT ["/usr/local/bin/aurora-php-entrypoint"]
