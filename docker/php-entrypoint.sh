#!/bin/sh
set -eu
mkdir -p /var/lib/fitness
chown -R www-data:www-data /var/lib/fitness
exec php-fpm -F