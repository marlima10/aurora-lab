<?php
declare(strict_types=1);

namespace Aurora\Services;

use Aurora\Database\Transaction;
use Aurora\Exceptions\ConflictException;
use Aurora\Repositories\FitnessStateRepository;
use Aurora\Repositories\TrainingPlanRepository;

final class FitnessSyncService
{
    public function __construct(
        private FitnessStateRepository $state,
        private TrainingPlanRepository $plans,
        private Transaction $transaction,
    ) {}

    public function read(): array
    {
        $state = $this->state->read();
        return $state === null ? ['ok' => true, 'initialized' => false] : ['ok' => true, 'initialized' => true] + $state;
    }

    public function import(array $people, array $entries): array
    {
        return $this->transaction->run(fn (): array => [
            'ok' => true, 'imported' => $this->state->import($people, $entries), 'initialized' => true,
        ]);
    }

    public function save(array $people, array $entries, ?int $expectedRevision): array
    {
        return $this->transaction->run(function () use ($people, $entries, $expectedRevision): array {
            $current = $this->state->read();
            if ($current !== null && $expectedRevision !== $current['revision']) {
                throw new ConflictException([
                    'conflict' => true, 'revision' => $current['revision'],
                    'people' => $current['people'], 'entries' => $current['entries'],
                ]);
            }
            $revision = ($current['revision'] ?? 0) + 1;
            $now = gmdate('c');
            $this->state->save($people, $entries, $revision, $now);
            $this->plans->pruneDeletedProfiles($people);
            return ['ok' => true, 'savedAt' => $now, 'revision' => $revision];
        });
    }

    public function merge(array $people, array $entries): array
    {
        return $this->transaction->run(function () use ($people, $entries): array {
            $current = $this->state->read();
            if ($current !== null) {
                $people = $this->mergeById($current['people'], $people);
                $entries = $this->mergeById($current['entries'], $entries);
            }
            $revision = ($current['revision'] ?? 0) + 1;
            $this->state->save($people, $entries, $revision, gmdate('c'));
            $this->plans->pruneDeletedProfiles($people);
            return ['ok' => true, 'merged' => true, 'revision' => $revision];
        });
    }

    private function mergeById(array $serverRows, array $clientRows): array
    {
        $merged = [];
        foreach ($clientRows as $row) {
            $merged[(string)$row['id']] = $row;
        }
        foreach ($serverRows as $row) {
            $id = (string)$row['id'];
            $local = $merged[$id] ?? null;
            if ($local === null || ($row['updatedAt'] ?? '') >= ($local['updatedAt'] ?? '')) {
                $merged[$id] = $row;
            }
        }
        return array_values($merged);
    }
}
