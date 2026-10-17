<?php
declare(strict_types=1);

namespace Aurora\Repositories;

use PDO;

final class TrainingPlanRepository
{
    public function __construct(private PDO $db) {}

    public function read(string $personId): array
    {
        $plans = [];
        $planQuery = $this->db->prepare('SELECT id, code, name FROM fitness_training_plans WHERE person_id = :person ORDER BY code');
        $planQuery->execute([':person' => $personId]);
        foreach ($planQuery->fetchAll() as $row) {
            $plans[$row['code']] = ['id' => $row['id'], 'code' => $row['code'], 'name' => $row['name'], 'exercises' => []];
        }
        $exerciseQuery = $this->db->prepare('SELECT e.id, p.code, e.catalog_id, COALESCE(c.muscle_group, e.muscle_group) AS muscle_group,
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
        $scheduleQuery = $this->db->prepare('SELECT s.weekday, p.code, s.start_time FROM fitness_plan_schedule s
            JOIN fitness_training_plans p ON p.id = s.plan_id WHERE s.person_id = :person ORDER BY s.weekday');
        $scheduleQuery->execute([':person' => $personId]);
        foreach ($scheduleQuery->fetchAll() as $row) {
            $schedule[] = ['weekday' => (int)$row['weekday'], 'planCode' => $row['code'], 'time' => $row['start_time']];
        }
        $revisionQuery = $this->db->prepare('SELECT revision FROM fitness_plan_revisions WHERE person_id = :person');
        $revisionQuery->execute([':person' => $personId]);
        return ['plans' => array_values($plans), 'schedule' => $schedule, 'revision' => (int)($revisionQuery->fetchColumn() ?: 0)];
    }

    public function pruneDeletedProfiles(array $people): void
    {
        $active = [];
        foreach ($people as $person) if (isset($person['id']) && empty($person['deletedAt'])) $active[(string)$person['id']] = true;
        $personIds = $this->db->query('SELECT person_id FROM fitness_plan_revisions UNION SELECT person_id FROM fitness_training_plans')->fetchAll(PDO::FETCH_COLUMN);
        $deletePlans = $this->db->prepare('DELETE FROM fitness_training_plans WHERE person_id = :person');
        $deleteRevision = $this->db->prepare('DELETE FROM fitness_plan_revisions WHERE person_id = :person');
        foreach ($personIds as $personId) {
            if (isset($active[(string)$personId])) continue;
            $deletePlans->execute([':person' => $personId]);
            $deleteRevision->execute([':person' => $personId]);
        }
    }

    public function replace(string $personId, array $planByCode, array $days): void
    {
        $delete = $this->db->prepare('DELETE FROM fitness_training_plans WHERE person_id = :person');
        $delete->execute([':person' => $personId]);
        $insertPlan = $this->db->prepare('INSERT INTO fitness_training_plans (id, person_id, code, name) VALUES (:id, :person, :code, :name)');
        $insertExercise = $this->db->prepare('INSERT INTO fitness_plan_exercises (id, plan_id, catalog_id, muscle_group, exercise_name, mode, sets, reps, duration_minutes, position) VALUES (:id, :plan, :catalog, :muscle, :name, :mode, :sets, :reps, :duration, :position)');
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
        $insertSchedule = $this->db->prepare('INSERT INTO fitness_plan_schedule (person_id, plan_id, weekday, start_time) VALUES (:person, :plan, :weekday, :time)');
        foreach ($days as $weekday => $slot) {
            $time = $slot['time'] ?? null;
            $insertSchedule->execute([':person' => $personId, ':plan' => $planIds[$slot['planCode']], ':weekday' => $weekday, ':time' => $time ?: null]);
        }

    }

    public function revision(string $personId): int
    {
        $query = $this->db->prepare('SELECT revision FROM fitness_plan_revisions WHERE person_id = :person');
        $query->execute([':person' => $personId]);
        return (int)($query->fetchColumn() ?: 0);
    }

    public function saveRevision(string $personId, int $revision): void
    {
        $query = $this->db->prepare('INSERT INTO fitness_plan_revisions (person_id, revision) VALUES (:person, :revision)
            ON CONFLICT(person_id) DO UPDATE SET revision = excluded.revision');
        $query->execute([':person' => $personId, ':revision' => $revision]);
    }
}
