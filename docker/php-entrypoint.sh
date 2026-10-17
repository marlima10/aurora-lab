#!/bin/sh
set -eu
export FITNESS_DB_PATH="${FITNESS_DB_PATH:-/var/lib/fitness/fitness.sqlite3}"
mkdir -p "$(dirname "$FITNESS_DB_PATH")"
chown -R www-data:www-data "$(dirname "$FITNESS_DB_PATH")"
su -s /bin/sh www-data -c 'php /var/www/backend/bin/migrate.php'
exec php-fpm -F
