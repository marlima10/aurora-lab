<?php
declare(strict_types=1);

namespace Aurora\Repositories;

use PDO;

final class ExerciseRepository
{
    public function __construct(private PDO $db) {}

    public function all(): array
    {
        $rows = $this->db->query('SELECT c.id, c.muscle_group AS muscleGroup, c.exercise_name AS name,
            c.mode, c.youtube_url AS youtubeUrl, c.updated_at AS updatedAt,
            (SELECT COUNT(*) FROM fitness_plan_exercises e WHERE e.catalog_id = c.id) AS planReferences
            FROM fitness_exercise_catalog c WHERE c.active = 1
            ORDER BY c.muscle_group COLLATE NOCASE, c.exercise_name COLLATE NOCASE')->fetchAll();
        foreach ($rows as &$row) {
            $row['planReferences'] = (int)$row['planReferences'];
        }
        return $rows;
    }

    public function find(string $id): ?array
    {
        $query = $this->db->prepare('SELECT id, muscle_group, exercise_name, mode, active FROM fitness_exercise_catalog WHERE id = :id');
        $query->execute([':id' => $id]);
        return $query->fetch() ?: null;
    }

    public function hasDuplicate(array $exercise): bool
    {
        $query = $this->db->prepare('SELECT id FROM fitness_exercise_catalog WHERE lower(muscle_group) = lower(:muscle)
            AND lower(exercise_name) = lower(:name) AND id <> :id AND active = 1');
        $query->execute([':muscle' => $exercise['muscleGroup'], ':name' => $exercise['name'], ':id' => $exercise['id']]);
        return $query->fetchColumn() !== false;
    }

    public function references(string $id): int
    {
        $query = $this->db->prepare('SELECT COUNT(*) FROM fitness_plan_exercises WHERE catalog_id = :id');
        $query->execute([':id' => $id]);
        return (int)$query->fetchColumn();
    }

    public function save(array $exercise): void
    {
        $query = $this->db->prepare('INSERT INTO fitness_exercise_catalog
            (id, muscle_group, exercise_name, mode, youtube_url, active, created_at, updated_at)
            VALUES (:id, :muscle, :name, :mode, :youtube, 1, :created, :updated)
            ON CONFLICT(id) DO UPDATE SET muscle_group = excluded.muscle_group, exercise_name = excluded.exercise_name,
                mode = excluded.mode, youtube_url = excluded.youtube_url, active = 1, updated_at = excluded.updated_at');
        $now = gmdate('c');
        $query->execute([
            ':id' => $exercise['id'], ':muscle' => $exercise['muscleGroup'], ':name' => $exercise['name'],
            ':mode' => $exercise['mode'], ':youtube' => $exercise['youtubeUrl'] ?: null,
            ':created' => $now, ':updated' => $now,
        ]);
    }

    public function delete(string $id): void
    {
        $query = $this->db->prepare('DELETE FROM fitness_exercise_catalog WHERE id = :id');
        $query->execute([':id' => $id]);
    }
}
