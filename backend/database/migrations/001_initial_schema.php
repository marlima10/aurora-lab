<?php
declare(strict_types=1);

return static function (PDO $db): void {
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
};
