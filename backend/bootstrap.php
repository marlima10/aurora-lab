<?php
declare(strict_types=1);

use Aurora\Database\Connection;
use Aurora\Database\Transaction;
use Aurora\Http\Application;
use Aurora\Http\Controllers\ExerciseController;
use Aurora\Http\Controllers\FitnessStateController;
use Aurora\Http\Controllers\TrainingPlanController;
use Aurora\Repositories\ExerciseRepository;
use Aurora\Repositories\FitnessStateRepository;
use Aurora\Repositories\TrainingPlanRepository;
use Aurora\Services\ExerciseCatalogService;
use Aurora\Services\FitnessSyncService;
use Aurora\Services\TrainingPlanService;

// Composer gera este autoloader durante o build do contêiner.
require_once __DIR__ . '/vendor/autoload.php';

return static function (): Application {
    $config = require __DIR__ . '/config/database.php';
    $db = Connection::open($config['path']);
    $transaction = new Transaction($db);
    $state = new FitnessStateRepository($db);
    $plans = new TrainingPlanRepository($db);
    $exercises = new ExerciseRepository($db);

    return new Application(
        new FitnessStateController(new FitnessSyncService($state, $plans, $transaction)),
        new TrainingPlanController(new TrainingPlanService($plans, $state, $exercises, $transaction)),
        new ExerciseController(new ExerciseCatalogService($exercises, $transaction)),
        require __DIR__ . '/routes/api.php',
    );
};
