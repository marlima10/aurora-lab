<?php
declare(strict_types=1);

use Aurora\Database\Connection;
use Aurora\Database\Migrator;
use Aurora\Http\Application;
use Aurora\Http\JsonResponse;

$createApplication = require dirname(__DIR__) . '/bootstrap.php';
$checks = 0;

function check(bool $condition, string $message): void
{
    global $checks;
    $checks++;
    if (!$condition) {
        throw new RuntimeException($message);
    }
}

function request(Application $app, array $body, int $status = 200): array
{
    $response = $app->handle('POST', [], json_encode($body, JSON_THROW_ON_ERROR));
    check($response->status === $status, 'Status inesperado: ' . json_encode($response->data, JSON_UNESCAPED_UNICODE));
    return $response->data;
}

function readPlans(Application $app): array
{
    return $app->handle('GET', ['action' => 'plans', 'person' => 'test-person'])->data;
}

// Caminhos próprios criados pelo teste. O banco configurado no ambiente nunca é usado.
$path = tempnam(sys_get_temp_dir(), 'aurora-test-');
$legacyPath = tempnam(sys_get_temp_dir(), 'aurora-legacy-');
$previousPath = getenv('FITNESS_DB_PATH');
$app = $legacyDb = $legacyApp = $db = null;

try {
    putenv('FITNESS_DB_PATH=' . $path);
    $db = Connection::open($path);
    $migrator = new Migrator($db, dirname(__DIR__) . '/database');
    $migrator->run();
    $app = $createApplication();
    check($app->handle('GET')->data === ['ok' => true, 'initialized' => false], 'Estado novo');
    check($app->handle('DELETE')->status === 405, 'Método não permitido');
    check($app->handle('POST', [], '{')->status === 400, 'JSON inválido');
    check($app->handle('POST', [], 'null')->status === 400, 'JSON escalar');
    check($app->handle('POST', [], str_repeat('x', 2000001))->status === 413, 'Limite do corpo');
    request($app, ['action' => ['invalid']], 400);
    request($app, ['action' => 'unknown'], 400);
    check($app->handle('GET', ['action' => 'plans'])->status === 400, 'Perfil obrigatório');

    $catalog = $app->handle('GET', ['action' => 'catalog'])->data['catalog'];
    check(count($catalog) === 37, 'Catálogo inicial');
    $people = [['id' => 'test-person', 'name' => 'Pessoa de teste', 'updatedAt' => '2020-01-01T00:00:00Z']];
    $entry = ['id' => 'entry-1', 'person' => 'test-person', 'date' => '2020-01-01', 'weight' => 80, 'updatedAt' => '2020-01-01T00:00:00Z'];
    $import = ['action' => 'import', 'people' => $people, 'entries' => [$entry]];
    check(request($app, $import)['imported'] === true, 'Primeira importação');
    check(request($app, $import)['imported'] === false, 'Importação não sobrescreve');
    $saved = request($app, ['people' => $people, 'entries' => [$entry], 'expectedRevision' => 1]);
    check($saved['revision'] === 2 && isset($saved['savedAt']), 'Gravação com revisão');
    $conflict = request($app, ['people' => [], 'entries' => [], 'expectedRevision' => 1], 409);
    check($conflict['conflict'] && $conflict['revision'] === 2 && $conflict['people'] === $people, 'Dados atuais no conflito');

    foreach ([['weight' => 0], ['weight' => 501], ['date' => '2020-02-30'], ['date' => '01/01/2020'], ['date' => '2999-01-01']] as $change) {
        request($app, ['people' => $people, 'entries' => [array_replace($entry, $change)], 'expectedRevision' => 2], 400);
    }
    request($app, ['people' => $people, 'entries' => [$entry, array_replace($entry, ['id' => 'entry-2'])], 'expectedRevision' => 2], 400);
    check($app->handle('GET')->data['revision'] === 2, 'Validações não alteram estado');

    $exercise = ['id' => 'test-exercise', 'muscleGroup' => 'Pernas', 'name' => 'Exercício teste', 'mode' => 'strength', 'youtubeUrl' => 'https://youtu.be/test'];
    check(request($app, ['action' => 'save_catalog_exercise', 'exercise' => $exercise])['exercise'] === $exercise, 'Cadastro de exercício');
    request($app, ['action' => 'save_catalog_exercise', 'exercise' => array_replace($exercise, ['id' => 'duplicate'])], 409);
    request($app, ['action' => 'save_catalog_exercise', 'exercise' => array_replace($exercise, ['youtubeUrl' => 'https://example.com/video'])], 400);
    request($app, ['action' => 'save_catalog_exercise', 'exercise' => array_replace($exercise, ['youtubeUrl' => []])], 400);

    $plans = [];
    foreach (['A', 'B', 'C', 'D'] as $code) {
        $plans[] = ['id' => 'plan-' . $code, 'code' => $code, 'name' => 'Ficha ' . $code, 'exercises' => []];
    }
    $plans[0]['exercises'][] = [
        'id' => 'plan-exercise', 'catalogId' => 'test-exercise', 'muscleGroup' => 'Outro',
        'name' => 'Nome desatualizado', 'mode' => 'strength', 'sets' => 3, 'reps' => 12,
    ];
    $planInput = [
        'action' => 'save_plans', 'personId' => 'test-person', 'plans' => $plans,
        'schedule' => [['weekday' => 1, 'planCode' => 'A', 'time' => '08:30']], 'expectedRevision' => 0,
    ];
    check(request($app, $planInput)['revision'] === 1, 'Salvar fichas e agenda');
    $planState = readPlans($app);
    check($planState['personExists'] && count($planState['plans']) === 4, 'Leitura das fichas');
    check($planState['plans'][0]['exercises'][0]['name'] === 'Exercício teste', 'Catálogo é fonte do nome');
    check($planState['schedule'][0]['time'] === '08:30', 'Horário da agenda');
    request($app, $planInput, 409);
    request($app, ['action' => 'delete_catalog_exercise', 'id' => 'test-exercise'], 409);
    request($app, ['action' => 'save_catalog_exercise', 'exercise' => array_replace($exercise, ['mode' => 'cardio'])], 409);
    $badTime = $planInput;
    $badTime['expectedRevision'] = 1;
    $badTime['schedule'][0]['time'] = '25:00';
    request($app, $badTime, 400);
    check(readPlans($app) === $planState, 'Agenda inválida preserva planos');

    $badCatalog = $planInput;
    $badCatalog['expectedRevision'] = 1;
    $badCatalog['plans'][0]['exercises'][0]['catalogId'] = 'missing';
    request($app, $badCatalog, 400);
    check(readPlans($app) === $planState, 'Erro de catálogo reverte transação');

    // Falha SQL depois de apagar as fichas deve restaurar tudo no rollback.
    $broken = $planInput;
    $broken['expectedRevision'] = 1;
    $broken['plans'][1]['exercises'] = $plans[0]['exercises'];
    request($app, $broken, 500);
    check(readPlans($app) === $planState, 'Falha SQL preserva fichas, agenda e revisão');

    $newPerson = array_replace($people[0], ['name' => 'Nome novo', 'updatedAt' => '2021-01-01T00:00:00Z']);
    check(request($app, ['action' => 'merge', 'people' => [$newPerson], 'entries' => []])['revision'] === 3, 'Merge incrementa revisão');
    check($app->handle('GET')->data['people'][0]['name'] === 'Nome novo', 'Merge escolhe registro mais recente');
    request($app, ['action' => 'merge', 'people' => [$people[0]], 'entries' => []]);
    check($app->handle('GET')->data['people'][0]['name'] === 'Nome novo', 'Merge não perde alteração mais recente');
    $deleted = array_replace($newPerson, ['deletedAt' => '2022-01-01T00:00:00Z']);
    request($app, ['people' => [$deleted], 'entries' => [$entry], 'expectedRevision' => 4]);
    check(readPlans($app)['plans'] === [] && readPlans($app)['revision'] === 0, 'Excluir perfil limpa planos e revisão');
    request($app, ['action' => 'delete_catalog_exercise', 'id' => 'test-exercise']);
    request($app, ['action' => 'delete_catalog_exercise', 'id' => 'leg-press']);
    $migrator->run();
    $afterRestart = $app->handle('GET', ['action' => 'catalog'])->data['catalog'];
    check(!in_array('leg-press', array_column($afterRestart, 'id'), true), 'Seed não recria exercício excluído');
    check((int)$db->query('SELECT COUNT(*) FROM schema_migrations')->fetchColumn() === 1, 'Migration idempotente');

    // Simula uma base anterior à coluna revision, sem tocar no banco pessoal.
    $legacyDb = Connection::open($legacyPath);
    $legacyDb->exec('CREATE TABLE fitness_state (id INTEGER PRIMARY KEY, people_json TEXT NOT NULL, entries_json TEXT NOT NULL, updated_at TEXT NOT NULL)');
    $insert = $legacyDb->prepare('INSERT INTO fitness_state VALUES (1, :people, :entries, :updated)');
    $insert->execute([':people' => json_encode($people), ':entries' => json_encode([$entry]), ':updated' => '2020-01-01']);
    $insert = null;
    $migration = new Migrator($legacyDb, dirname(__DIR__) . '/database');
    $migration->run();
    $migration->run();
    putenv('FITNESS_DB_PATH=' . $legacyPath);
    $legacyApp = $createApplication();
    $legacyState = $legacyApp->handle('GET')->data;
    check($legacyState['people'] === $people && $legacyState['entries'] === [$entry], 'Migration preserva dados antigos');
    check($legacyState['revision'] === 1, 'Migration acrescenta revisão');

    echo "OK: {$checks} verificações de integração.\n";
} finally {
    $app = $legacyApp = $db = $legacyDb = $migrator = $migration = null;
    gc_collect_cycles();
    putenv($previousPath === false ? 'FITNESS_DB_PATH' : 'FITNESS_DB_PATH=' . $previousPath);
    foreach ([$path, $legacyPath] as $temporaryPath) {
        foreach (['', '-wal', '-shm'] as $suffix) {
            if (is_file($temporaryPath . $suffix)) {
                unlink($temporaryPath . $suffix);
            }
        }
    }
}
