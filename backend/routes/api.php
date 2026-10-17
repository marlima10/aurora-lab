<?php
declare(strict_types=1);

// Ações existentes são mantidas para preservar o frontend e o cache PWA.
return [
    'GET' => [
        'catalog' => ['exercises', 'index'],
        'plans' => ['plans', 'show'],
        '*' => ['state', 'show'],
    ],
    'POST' => [
        'save_catalog_exercise' => ['exercises', 'save'],
        'delete_catalog_exercise' => ['exercises', 'delete'],
        'save_plans' => ['plans', 'save'],
        'save' => ['state', 'save'],
        'import' => ['state', 'import'],
        'merge' => ['state', 'merge'],
    ],
];
