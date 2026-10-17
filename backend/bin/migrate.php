<?php
declare(strict_types=1);

use Aurora\Database\Connection;
use Aurora\Database\Migrator;

require dirname(__DIR__) . '/vendor/autoload.php';
$config = require dirname(__DIR__) . '/config/database.php';
(new Migrator(Connection::open($config['path']), dirname(__DIR__) . '/database'))->run();
echo "Migrations concluídas.\n";
