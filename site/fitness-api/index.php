<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate');
header('X-Content-Type-Options: nosniff');

$dbPath = '/var/lib/fitness/fitness.sqlite3';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

function respond(int $status, array $data): void {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function readPlanState(PDO $db, string $personId): array {
    $plans = [];
    $planQuery = $db->prepare('SELECT id, code, name FROM fitness_training_plans WHERE person_id = :person ORDER BY code');
    $planQuery->execute([':person' => $personId]);
    foreach ($planQuery->fetchAll() as $row) {
        $plans[$row['code']] = ['id' => $row['id'], 'code' => $row['code'], 'name' => $row['name'], 'exercises' => []];
    }
    $exerciseQuery = $db->prepare('SELECT e.id, p.code, e.catalog_id, COALESCE(c.muscle_group, e.muscle_group) AS muscle_group,
        COALESCE(c.exercise_name, e.exercise_name) AS exercise_name, COALESCE(c.mode, e.mode) AS mode,
        COALESCE(c.youtube_url, \'\') AS youtube_url, e.sets, e.reps, e.duration_minutes, e.position
        FROM fitness_plan_exercises e JOIN fitness_training_plans p ON p.id = e.plan_id
        LEFT JOIN fitness_exercise_catalog c ON c.id = e.catalog_id
        WHERE p.person_id = :person ORDER BY p.code, e.position, e.id');
    $exerciseQuery->execute([':person' => $personId]);
    foreach ($exerciseQuery->fetchAll() as $row) {
        if (!isset($plans[$row['code']])) continue;
        $plans[$row['code']]['exercises'][] = [
            'id' => $row['id'], 'catalogId' => $row['catalog_id'], 'muscleGroup' => $row['muscle_group'],
            'name' => $row['exercise_name'], 'mode' => $row['mode'], 'youtubeUrl' => $row['youtube_url'], 'sets' => $row['sets'] === null ? null : (int)$row['sets'],
            'reps' => $row['reps'] === null ? null : (int)$row['reps'],
            'durationMinutes' => $row['duration_minutes'] === null ? null : (int)$row['duration_minutes'],
            'position' => (int)$row['position'],
        ];
    }
    $schedule = [];
    $scheduleQuery = $db->prepare('SELECT s.weekday, p.code, s.start_time FROM fitness_plan_schedule s
        JOIN fitness_training_plans p ON p.id = s.plan_id WHERE s.person_id = :person ORDER BY s.weekday');
    $scheduleQuery->execute([':person' => $personId]);
    foreach ($scheduleQuery->fetchAll() as $row) {
        $schedule[] = ['weekday' => (int)$row['weekday'], 'planCode' => $row['code'], 'time' => $row['start_time']];
    }
    $revisionQuery = $db->prepare('SELECT revision FROM fitness_plan_revisions WHERE person_id = :person');
    $revisionQuery->execute([':person' => $personId]);
    return ['plans' => array_values($plans), 'schedule' => $schedule, 'revision' => (int)($revisionQuery->fetchColumn() ?: 0)];
}

function pruneDeletedPlanProfiles(PDO $db, array $people): void {
    $active = [];
    foreach ($people as $person) if (isset($person['id']) && empty($person['deletedAt'])) $active[(string)$person['id']] = true;
    $personIds = $db->query('SELECT person_id FROM fitness_plan_revisions UNION SELECT person_id FROM fitness_training_plans')->fetchAll(PDO::FETCH_COLUMN);
    $deletePlans = $db->prepare('DELETE FROM fitness_training_plans WHERE person_id = :person');
    $deleteRevision = $db->prepare('DELETE FROM fitness_plan_revisions WHERE person_id = :person');
    foreach ($personIds as $personId) {
        if (isset($active[(string)$personId])) continue;
        $deletePlans->execute([':person' => $personId]);
        $deleteRevision->execute([':person' => $personId]);
    }
}

try {
    $db = new PDO('sqlite:' . $dbPath, null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $db->exec('PRAGMA busy_timeout = 5000');
    $db->exec('PRAGMA journal_mode = WAL');
    $db->exec('PRAGMA foreign_keys = ON');
    $db->exec('CREATE TABLE IF NOT EXISTS fitness_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        people_json TEXT NOT NULL,
        entries_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        revision INTEGER NOT NULL DEFAULT 1
    )');
    $columns = $db->query('PRAGMA table_info(fitness_state)')->fetchAll();
    $hasRevision = false;
    foreach ($columns as $column) if ($column['name'] === 'revision') $hasRevision = true;
    if (!$hasRevision) $db->exec('ALTER TABLE fitness_state ADD COLUMN revision INTEGER NOT NULL DEFAULT 1');

    $db->exec('CREATE TABLE IF NOT EXISTS fitness_training_plans (
        id TEXT PRIMARY KEY,
        person_id TEXT NOT NULL,
        code TEXT NOT NULL CHECK (code IN (\'A\', \'B\', \'C\', \'D\')),
        name TEXT NOT NULL,
        UNIQUE(person_id, code)
    )');
    $db->exec('CREATE TABLE IF NOT EXISTS fitness_plan_exercises (
        id TEXT PRIMARY KEY,
        plan_id TEXT NOT NULL REFERENCES fitness_training_plans(id) ON DELETE CASCADE,
        catalog_id TEXT NOT NULL,
        muscle_group TEXT NOT NULL,
        exercise_name TEXT NOT NULL,
        mode TEXT NOT NULL CHECK (mode IN (\'strength\', \'cardio\')),
        sets INTEGER,
        reps INTEGER,
        duration_minutes INTEGER,
        position INTEGER NOT NULL DEFAULT 0
    )');
    $db->exec('CREATE TABLE IF NOT EXISTS fitness_plan_schedule (
        person_id TEXT NOT NULL,
        plan_id TEXT NOT NULL REFERENCES fitness_training_plans(id) ON DELETE CASCADE,
        weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
        start_time TEXT,
        PRIMARY KEY(person_id, weekday)
    )');
    $db->exec('CREATE TABLE IF NOT EXISTS fitness_plan_revisions (
        person_id TEXT PRIMARY KEY,
        revision INTEGER NOT NULL DEFAULT 0
    )');
    $db->exec('CREATE TABLE IF NOT EXISTS fitness_exercise_catalog (
        id TEXT PRIMARY KEY,
        muscle_group TEXT NOT NULL,
        exercise_name TEXT NOT NULL,
        mode TEXT NOT NULL CHECK (mode IN (\'strength\', \'cardio\')),
        youtube_url TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(muscle_group, exercise_name)
    )');
    $exerciseSeeds = [
        ['leg-press','Pernas','Leg press','strength'], ['box-squat','Pernas','Agachamento até um banco','strength'], ['goblet-squat','Pernas','Agachamento goblet','strength'], ['leg-extension','Pernas','Cadeira extensora','strength'], ['seated-leg-curl','Pernas','Mesa flexora','strength'], ['hip-thrust','Pernas','Elevação pélvica','strength'], ['romanian-deadlift','Pernas','Levantamento terra romeno com halteres','strength'], ['hip-abduction','Pernas','Abdução de quadril na máquina','strength'],
        ['lat-pulldown','Costas','Puxada frontal','strength'], ['seated-row','Costas','Remada baixa','strength'], ['chest-supported-row','Costas','Remada com apoio no peito','strength'], ['face-pull','Costas','Face pull','strength'], ['straight-arm-pulldown','Costas','Puxada com braços estendidos','strength'], ['back-extension','Costas','Extensão lombar','strength'],
        ['chest-press','Peito','Supino na máquina','strength'], ['bench-press','Peito','Supino com barra','strength'], ['incline-dumbbell-press','Peito','Supino inclinado com halteres','strength'], ['push-up','Peito','Flexão de braços','strength'], ['cable-fly','Peito','Crucifixo no cabo','strength'],
        ['seated-shoulder-press','Ombros','Desenvolvimento sentado','strength'], ['lateral-raise','Ombros','Elevação lateral','strength'], ['reverse-fly','Ombros','Crucifixo inverso','strength'],
        ['biceps-curl','Braços','Rosca bíceps','strength'], ['hammer-curl','Braços','Rosca martelo','strength'], ['triceps-pushdown','Braços','Tríceps na polia','strength'], ['overhead-triceps','Braços','Tríceps acima da cabeça','strength'],
        ['dead-bug','Core','Dead bug','strength'], ['pallof-press','Core','Pallof press','strength'], ['bird-dog','Core','Bird dog','strength'], ['abdominal-crunch','Core','Abdominal crunch','strength'], ['reverse-crunch','Core','Abdominal reverso','strength'], ['heel-taps','Core','Toque nos calcanhares deitado','strength'],
        ['stationary-bike','Cardio','Bicicleta ergométrica','cardio'], ['treadmill-walk','Cardio','Caminhada na esteira','cardio'], ['elliptical','Cardio','Elíptico','cardio'], ['rowing-machine','Cardio','Remo ergométrico','cardio'], ['light-run','Cardio','Corrida leve','cardio'],
    ];
    $seedExercise = $db->prepare('INSERT OR IGNORE INTO fitness_exercise_catalog (id, muscle_group, exercise_name, mode, youtube_url, active, created_at, updated_at) VALUES (:id, :muscle, :name, :mode, NULL, 1, :created, :updated)');
    foreach ($exerciseSeeds as [$id, $muscle, $name, $mode]) $seedExercise->execute([':id' => $id, ':muscle' => $muscle, ':name' => $name, ':mode' => $mode, ':created' => gmdate('c'), ':updated' => gmdate('c')]);

    if ($method === 'GET') {
        if (($_GET['action'] ?? '') === 'catalog') {
            $catalog = $db->query('SELECT c.id, c.muscle_group AS muscleGroup, c.exercise_name AS name, c.mode, c.youtube_url AS youtubeUrl, c.updated_at AS updatedAt,
                (SELECT COUNT(*) FROM fitness_plan_exercises e WHERE e.catalog_id = c.id) AS planReferences
                FROM fitness_exercise_catalog c WHERE c.active = 1 ORDER BY c.muscle_group COLLATE NOCASE, c.exercise_name COLLATE NOCASE')->fetchAll();
            foreach ($catalog as &$item) $item['planReferences'] = (int)$item['planReferences'];
            unset($item);
            respond(200, ['ok' => true, 'catalog' => $catalog]);
        }
        if (($_GET['action'] ?? '') === 'plans') {
            $personId = $_GET['person'] ?? '';
            if (!is_string($personId) || $personId === '') respond(400, ['ok' => false, 'error' => 'Perfil não informado']);
            $stateRow = $db->query('SELECT people_json FROM fitness_state WHERE id = 1')->fetch();
            $people = $stateRow ? json_decode($stateRow['people_json'], true, 512, JSON_THROW_ON_ERROR) : [];
            $personExists = false;
            foreach ($people as $person) if (($person['id'] ?? null) === $personId && empty($person['deletedAt'])) $personExists = true;
            respond(200, ['ok' => true, 'personExists' => $personExists] + readPlanState($db, $personId));
        }
        $row = $db->query('SELECT people_json, entries_json, updated_at, revision FROM fitness_state WHERE id = 1')->fetch();
        if (!$row) respond(200, ['ok' => true, 'initialized' => false]);
        respond(200, [
            'ok' => true,
            'initialized' => true,
            'people' => json_decode($row['people_json'], true, 512, JSON_THROW_ON_ERROR),
            'entries' => json_decode($row['entries_json'], true, 512, JSON_THROW_ON_ERROR),
            'updatedAt' => $row['updated_at'],
            'revision' => (int)$row['revision'],
        ]);
    }

    if ($method !== 'POST') respond(405, ['ok' => false, 'error' => 'Método não permitido']);
    $raw = file_get_contents('php://input');
    if ($raw === false || strlen($raw) > 2000000) respond(413, ['ok' => false, 'error' => 'Dados ausentes ou acima de 2 MB']);
    $body = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
    $action = $body['action'] ?? 'save';
    if ($action === 'save_catalog_exercise') {
        $exercise = $body['exercise'] ?? null;
        if (!is_array($exercise) || !isset($exercise['id'], $exercise['muscleGroup'], $exercise['name'], $exercise['mode']) || !is_string($exercise['id']) || !is_string($exercise['muscleGroup']) || !is_string($exercise['name']) || !in_array($exercise['mode'], ['strength','cardio'], true)) {
            respond(400, ['ok' => false, 'error' => 'Cadastro de exercício inválido']);
        }
        $id = trim($exercise['id']); $muscle = trim($exercise['muscleGroup']); $name = trim($exercise['name']); $mode = $exercise['mode']; $youtube = trim((string)($exercise['youtubeUrl'] ?? ''));
        if ($id === '' || $muscle === '' || $name === '' || strlen($id) > 100 || strlen($muscle) > 80 || strlen($name) > 140) respond(400, ['ok' => false, 'error' => 'Preencha músculo/grupo e nome do exercício']);
        if ($youtube !== '') {
            $parts = parse_url($youtube);
            $hosts = ['youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.youtu.be','youtube-nocookie.com','www.youtube-nocookie.com'];
            $host = strtolower((string)($parts['host'] ?? ''));
            if (($parts['scheme'] ?? '') !== 'https' || !in_array($host, $hosts, true) || strlen($youtube) > 500) respond(400, ['ok' => false, 'error' => 'Use um link HTTPS válido do YouTube']);
        }
        $duplicate = $db->prepare('SELECT id FROM fitness_exercise_catalog WHERE lower(muscle_group) = lower(:muscle) AND lower(exercise_name) = lower(:name) AND id <> :id AND active = 1');
        $duplicate->execute([':muscle' => $muscle, ':name' => $name, ':id' => $id]);
        if ($duplicate->fetchColumn()) respond(409, ['ok' => false, 'error' => 'Já existe um exercício com esse nome nesse grupo muscular']);
        $current = $db->prepare('SELECT mode FROM fitness_exercise_catalog WHERE id = :id');
        $current->execute([':id' => $id]); $oldMode = $current->fetchColumn();
        if ($oldMode !== false && $oldMode !== $mode) {
            $references = $db->prepare('SELECT COUNT(*) FROM fitness_plan_exercises WHERE catalog_id = :id');
            $references->execute([':id' => $id]);
            if ((int)$references->fetchColumn() > 0) respond(409, ['ok' => false, 'error' => 'Este exercício já está em uma ficha. Remova-o dos planos antes de mudar entre força e cardio.']);
        }
        $save = $db->prepare('INSERT INTO fitness_exercise_catalog (id, muscle_group, exercise_name, mode, youtube_url, active, created_at, updated_at)
            VALUES (:id, :muscle, :name, :mode, :youtube, 1, :created, :updated)
            ON CONFLICT(id) DO UPDATE SET muscle_group = excluded.muscle_group, exercise_name = excluded.exercise_name,
            mode = excluded.mode, youtube_url = excluded.youtube_url, active = 1, updated_at = excluded.updated_at');
        $now = gmdate('c');
        $save->execute([':id' => $id, ':muscle' => $muscle, ':name' => $name, ':mode' => $mode, ':youtube' => $youtube ?: null, ':created' => $now, ':updated' => $now]);
        respond(200, ['ok' => true, 'exercise' => ['id' => $id, 'muscleGroup' => $muscle, 'name' => $name, 'mode' => $mode, 'youtubeUrl' => $youtube]]);
    }
    if ($action === 'delete_catalog_exercise') {
        $id = $body['id'] ?? null;
        if (!is_string($id) || $id === '') respond(400, ['ok' => false, 'error' => 'Exercício não informado']);
        $references = $db->prepare('SELECT COUNT(*) FROM fitness_plan_exercises WHERE catalog_id = :id');
        $references->execute([':id' => $id]);
        if ((int)$references->fetchColumn() > 0) respond(409, ['ok' => false, 'error' => 'Este exercício está em uma ou mais fichas. Retire-o dos planos antes de excluir.']);
        $delete = $db->prepare('DELETE FROM fitness_exercise_catalog WHERE id = :id');
        $delete->execute([':id' => $id]);
        respond(200, ['ok' => true]);
    }
    if ($action === 'save_plans') {
        $personId = $body['personId'] ?? null;
        $plans = $body['plans'] ?? null;
        $schedule = $body['schedule'] ?? null;
        $expectedRevision = isset($body['expectedRevision']) ? (int)$body['expectedRevision'] : -1;
        if (!is_string($personId) || $personId === '' || !is_array($plans) || count($plans) !== 4 || !is_array($schedule) || count($schedule) > 7) {
            respond(400, ['ok' => false, 'error' => 'Plano ou agenda em formato inválido']);
        }
        $planByCode = [];
        $catalogLookup = $db->prepare('SELECT muscle_group, exercise_name, mode FROM fitness_exercise_catalog WHERE id = :id AND active = 1');
        foreach ($plans as $plan) {
            if (!is_array($plan) || !isset($plan['id'], $plan['code'], $plan['name'], $plan['exercises']) || !is_string($plan['id']) || !is_string($plan['code']) || !is_string($plan['name']) || !is_array($plan['exercises']) || !in_array($plan['code'], ['A','B','C','D'], true) || isset($planByCode[$plan['code']]) || count($plan['exercises']) > 40) {
                respond(400, ['ok' => false, 'error' => 'Ficha de treino inválida']);
            }
            $planByCode[$plan['code']] = $plan;
            foreach ($plan['exercises'] as &$exercise) {
                if (!is_array($exercise) || !isset($exercise['id'], $exercise['catalogId'], $exercise['muscleGroup'], $exercise['name'], $exercise['mode']) || !is_string($exercise['id']) || !is_string($exercise['catalogId']) || !is_string($exercise['muscleGroup']) || !is_string($exercise['name']) || !in_array($exercise['mode'], ['strength','cardio'], true)) {
                    respond(400, ['ok' => false, 'error' => 'Exercício inválido']);
                }
                $catalogLookup->execute([':id' => $exercise['catalogId']]);
                $catalogItem = $catalogLookup->fetch();
                if (!$catalogItem) respond(400, ['ok' => false, 'error' => 'O exercício selecionado não está mais no catálogo SQL']);
                if ($exercise['mode'] !== $catalogItem['mode']) respond(400, ['ok' => false, 'error' => 'O tipo do exercício mudou no catálogo. Recarregue o plano e tente novamente.']);
                $exercise['muscleGroup'] = $catalogItem['muscle_group'];
                $exercise['name'] = $catalogItem['exercise_name'];
                $exercise['mode'] = $catalogItem['mode'];
                if ($exercise['mode'] === 'strength' && (!isset($exercise['sets'], $exercise['reps']) || (int)$exercise['sets'] < 1 || (int)$exercise['sets'] > 20 || (int)$exercise['reps'] < 1 || (int)$exercise['reps'] > 100)) {
                    respond(400, ['ok' => false, 'error' => 'Informe séries e repetições válidas']);
                }
                if ($exercise['mode'] === 'cardio' && (!isset($exercise['durationMinutes']) || (int)$exercise['durationMinutes'] < 1 || (int)$exercise['durationMinutes'] > 1440)) {
                    respond(400, ['ok' => false, 'error' => 'Informe o tempo de cardio em minutos']);
                }
            }
            unset($exercise);
        }
        if (count($planByCode) !== 4) respond(400, ['ok' => false, 'error' => 'As fichas A, B, C e D são obrigatórias']);
        $days = [];
        foreach ($schedule as $slot) {
            if (!is_array($slot) || !isset($slot['weekday'], $slot['planCode']) || !is_numeric($slot['weekday']) || !is_string($slot['planCode']) || (int)$slot['weekday'] < 0 || (int)$slot['weekday'] > 6 || !isset($planByCode[$slot['planCode']]) || isset($days[(int)$slot['weekday']])) {
                respond(400, ['ok' => false, 'error' => 'Agenda semanal inválida']);
            }
            $days[(int)$slot['weekday']] = $slot;
        }
        $db->exec('BEGIN IMMEDIATE');
        $stateRow = $db->query('SELECT people_json FROM fitness_state WHERE id = 1')->fetch();
        $people = $stateRow ? json_decode($stateRow['people_json'], true, 512, JSON_THROW_ON_ERROR) : [];
        $personExists = false;
        foreach ($people as $person) if (($person['id'] ?? null) === $personId && empty($person['deletedAt'])) $personExists = true;
        if (!$personExists) { $db->exec('ROLLBACK'); respond(409, ['ok' => false, 'error' => 'Esse perfil ainda não está gravado no SQL. Abra o Fitness conectado e tente novamente.']); }
        $revisionQuery = $db->prepare('SELECT revision FROM fitness_plan_revisions WHERE person_id = :person');
        $revisionQuery->execute([':person' => $personId]);
        $currentRevision = (int)($revisionQuery->fetchColumn() ?: 0);
        if ($expectedRevision !== $currentRevision) { $db->exec('ROLLBACK'); respond(409, ['ok' => false, 'conflict' => true, 'error' => 'O plano mudou em outro aparelho. Recarregue a página antes de salvar.']); }
        $delete = $db->prepare('DELETE FROM fitness_training_plans WHERE person_id = :person');
        $delete->execute([':person' => $personId]);
        $insertPlan = $db->prepare('INSERT INTO fitness_training_plans (id, person_id, code, name) VALUES (:id, :person, :code, :name)');
        $insertExercise = $db->prepare('INSERT INTO fitness_plan_exercises (id, plan_id, catalog_id, muscle_group, exercise_name, mode, sets, reps, duration_minutes, position) VALUES (:id, :plan, :catalog, :muscle, :name, :mode, :sets, :reps, :duration, :position)');
        foreach ($planByCode as $plan) {
            $insertPlan->execute([':id' => $plan['id'], ':person' => $personId, ':code' => $plan['code'], ':name' => substr(trim($plan['name']), 0, 120)]);
            foreach (array_values($plan['exercises']) as $position => $exercise) {
                $insertExercise->execute([
                    ':id' => $exercise['id'], ':plan' => $plan['id'], ':catalog' => $exercise['catalogId'],
                    ':muscle' => substr($exercise['muscleGroup'], 0, 100), ':name' => substr($exercise['name'], 0, 160),
                    ':mode' => $exercise['mode'], ':sets' => $exercise['mode'] === 'strength' ? (int)$exercise['sets'] : null,
                    ':reps' => $exercise['mode'] === 'strength' ? (int)$exercise['reps'] : null,
                    ':duration' => $exercise['mode'] === 'cardio' ? (int)$exercise['durationMinutes'] : null,
                    ':position' => $position,
                ]);
            }
        }
        $planIds = [];
        foreach ($planByCode as $plan) $planIds[$plan['code']] = $plan['id'];
        $insertSchedule = $db->prepare('INSERT INTO fitness_plan_schedule (person_id, plan_id, weekday, start_time) VALUES (:person, :plan, :weekday, :time)');
        foreach ($days as $weekday => $slot) {
            $time = $slot['time'] ?? null;
            if ($time !== null && $time !== '' && (!is_string($time) || !preg_match('/^(?:[01]\d|2[0-3]):[0-5]\d$/', $time))) { $db->exec('ROLLBACK'); respond(400, ['ok' => false, 'error' => 'Horário inválido']); }
            $insertSchedule->execute([':person' => $personId, ':plan' => $planIds[$slot['planCode']], ':weekday' => $weekday, ':time' => $time ?: null]);
        }
        $nextRevision = $currentRevision + 1;
        $saveRevision = $db->prepare('INSERT INTO fitness_plan_revisions (person_id, revision) VALUES (:person, :revision) ON CONFLICT(person_id) DO UPDATE SET revision = excluded.revision');
        $saveRevision->execute([':person' => $personId, ':revision' => $nextRevision]);
        $db->exec('COMMIT');
        respond(200, ['ok' => true, 'revision' => $nextRevision]);
    }
    $people = $body['people'] ?? null;
    $entries = $body['entries'] ?? null;
    if (!is_array($people) || !is_array($entries) || count($people) > 500 || count($entries) > 50000) {
        respond(400, ['ok' => false, 'error' => 'Formato de dados inválido']);
    }
    foreach ($people as $person) {
        if (!is_array($person) || !isset($person['id'], $person['name']) || !is_string($person['id']) || !is_string($person['name'])) {
            respond(400, ['ok' => false, 'error' => 'Cadastro de pessoa inválido']);
        }
    }
    $activePersonDates = [];
    foreach ($entries as $entry) {
        if (!is_array($entry) || !isset($entry['id'], $entry['person']) || !is_string($entry['id']) || !is_string($entry['person'])) {
            respond(400, ['ok' => false, 'error' => 'Registro de treino/peso inválido']);
        }
        if ($action === 'save') {
            $date = $entry['date'] ?? null;
            if ($date !== null && $date !== '') {
                if (!is_string($date) || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) {
                    respond(400, ['ok' => false, 'error' => 'Use uma data válida no formato AAAA-MM-DD']);
                }
                $parsedDate = DateTimeImmutable::createFromFormat('!Y-m-d', $date);
                $dateErrors = DateTimeImmutable::getLastErrors();
                if (!$parsedDate || ($dateErrors !== false && ($dateErrors['warning_count'] > 0 || $dateErrors['error_count'] > 0)) || $parsedDate->format('Y-m-d') !== $date) {
                    respond(400, ['ok' => false, 'error' => 'A data informada não existe no calendário']);
                }
                if ($date > date('Y-m-d')) respond(400, ['ok' => false, 'error' => 'Não é permitido salvar registros em datas futuras']);
                if (empty($entry['deletedAt'])) {
                    $personDate = $entry['person'] . '|' . $date;
                    if (isset($activePersonDates[$personDate])) respond(400, ['ok' => false, 'error' => 'Já existe um registro ativo para essa pessoa e data']);
                    $activePersonDates[$personDate] = true;
                }
            }
            $weight = $entry['weight'] ?? null;
            if ($weight !== null && $weight !== '' && (!is_numeric($weight) || (float)$weight < 1 || (float)$weight > 500)) {
                respond(400, ['ok' => false, 'error' => 'O peso deve estar entre 1 e 500 kg']);
            }
        }
    }

    $peopleJson = json_encode(array_values($people), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    $entriesJson = json_encode(array_values($entries), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    $db->exec('BEGIN IMMEDIATE');
    if ($action === 'import') {
        $insert = $db->prepare('INSERT OR IGNORE INTO fitness_state (id, people_json, entries_json, updated_at, revision) VALUES (1, :people, :entries, :updated, 1)');
        $insert->execute([':people' => $peopleJson, ':entries' => $entriesJson, ':updated' => gmdate('c')]);
        $inserted = $insert->rowCount() === 1;
        $db->exec('COMMIT');
        respond(200, ['ok' => true, 'imported' => $inserted, 'initialized' => true]);
    }
    if ($action === 'merge') {
        $current = $db->query('SELECT people_json, entries_json FROM fitness_state WHERE id = 1')->fetch();
        $mergeById = static function (array $serverRows, array $clientRows): array {
            $merged = [];
            foreach ($clientRows as $row) $merged[(string)$row['id']] = $row;
            foreach ($serverRows as $row) {
                $id = (string)$row['id'];
                $local = $merged[$id] ?? null;
                if ($local === null || (($row['updatedAt'] ?? '') >= ($local['updatedAt'] ?? ''))) $merged[$id] = $row;
            }
            return array_values($merged);
        };
        if ($current) {
            $peopleJson = json_encode($mergeById(json_decode($current['people_json'], true, 512, JSON_THROW_ON_ERROR), $people), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
            $entriesJson = json_encode($mergeById(json_decode($current['entries_json'], true, 512, JSON_THROW_ON_ERROR), $entries), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
        }
        $currentRevision = (int)($db->query('SELECT revision FROM fitness_state WHERE id = 1')->fetchColumn() ?: 0);
        $upsert = $db->prepare('INSERT INTO fitness_state (id, people_json, entries_json, updated_at, revision)
            VALUES (1, :people, :entries, :updated, :revision)
            ON CONFLICT(id) DO UPDATE SET people_json = excluded.people_json,
            entries_json = excluded.entries_json, updated_at = excluded.updated_at, revision = excluded.revision');
        $upsert->execute([':people' => $peopleJson, ':entries' => $entriesJson, ':updated' => gmdate('c'), ':revision' => $currentRevision + 1]);
        pruneDeletedPlanProfiles($db, json_decode($peopleJson, true, 512, JSON_THROW_ON_ERROR));
        $db->exec('COMMIT');
        respond(200, ['ok' => true, 'merged' => true, 'revision' => $currentRevision + 1]);
    }
    if ($action !== 'save') {
        $db->exec('ROLLBACK');
        respond(400, ['ok' => false, 'error' => 'Ação inválida']);
    }
    $current = $db->query('SELECT people_json, entries_json, revision FROM fitness_state WHERE id = 1')->fetch();
    $expectedRevision = isset($body['expectedRevision']) ? (int)$body['expectedRevision'] : null;
    if ($current && $expectedRevision !== (int)$current['revision']) {
        $db->exec('ROLLBACK');
        respond(409, [
            'ok' => false,
            'conflict' => true,
            'revision' => (int)$current['revision'],
            'people' => json_decode($current['people_json'], true, 512, JSON_THROW_ON_ERROR),
            'entries' => json_decode($current['entries_json'], true, 512, JSON_THROW_ON_ERROR),
        ]);
    }
    $nextRevision = $current ? ((int)$current['revision'] + 1) : 1;
    $upsert = $db->prepare('INSERT INTO fitness_state (id, people_json, entries_json, updated_at, revision)
        VALUES (1, :people, :entries, :updated, :revision)
        ON CONFLICT(id) DO UPDATE SET people_json = excluded.people_json,
        entries_json = excluded.entries_json, updated_at = excluded.updated_at, revision = excluded.revision');
    $upsert->execute([':people' => $peopleJson, ':entries' => $entriesJson, ':updated' => gmdate('c'), ':revision' => $nextRevision]);
    pruneDeletedPlanProfiles($db, $people);
    $db->exec('COMMIT');
    respond(200, ['ok' => true, 'savedAt' => gmdate('c'), 'revision' => $nextRevision]);
} catch (JsonException $e) {
    respond(400, ['ok' => false, 'error' => 'JSON inválido']);
} catch (Throwable $e) {
    error_log('Fitness API: ' . $e->getMessage());
    respond(500, ['ok' => false, 'error' => 'Falha ao acessar o banco Fitness']);
}
