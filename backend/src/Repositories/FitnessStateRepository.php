<?php
declare(strict_types=1);

namespace Aurora\Repositories;

use PDO;

final class FitnessStateRepository
{
    public function __construct(private PDO $db) {}

    public function read(): ?array
    {
        $row = $this->db->query('SELECT people_json, entries_json, updated_at, revision FROM fitness_state WHERE id = 1')->fetch();
        if (!$row) {
            return null;
        }
        return [
            'people' => json_decode($row['people_json'], true, 512, JSON_THROW_ON_ERROR),
            'entries' => json_decode($row['entries_json'], true, 512, JSON_THROW_ON_ERROR),
            'updatedAt' => $row['updated_at'],
            'revision' => (int)$row['revision'],
        ];
    }

    public function personExists(string $personId): bool
    {
        foreach (($this->read()['people'] ?? []) as $person) {
            if (($person['id'] ?? null) === $personId && empty($person['deletedAt'])) {
                return true;
            }
        }
        return false;
    }

    public function import(array $people, array $entries): bool
    {
        $query = $this->db->prepare('INSERT OR IGNORE INTO fitness_state
            (id, people_json, entries_json, updated_at, revision) VALUES (1, :people, :entries, :updated, 1)');
        $query->execute($this->parameters($people, $entries, gmdate('c')));
        return $query->rowCount() === 1;
    }

    public function save(array $people, array $entries, int $revision, string $updatedAt): void
    {
        $query = $this->db->prepare('INSERT INTO fitness_state (id, people_json, entries_json, updated_at, revision)
            VALUES (1, :people, :entries, :updated, :revision)
            ON CONFLICT(id) DO UPDATE SET people_json = excluded.people_json,
                entries_json = excluded.entries_json, updated_at = excluded.updated_at, revision = excluded.revision');
        $query->execute($this->parameters($people, $entries, $updatedAt) + [':revision' => $revision]);
    }

    private function parameters(array $people, array $entries, string $updatedAt): array
    {
        $flags = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR;
        return [
            ':people' => json_encode(array_values($people), $flags),
            ':entries' => json_encode(array_values($entries), $flags),
            ':updated' => $updatedAt,
        ];
    }
}
