<?php
declare(strict_types=1);

return static function (PDO $db): void {
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

};
