<?php
declare(strict_types=1);

namespace Aurora\Services;

use Aurora\Database\Transaction;
use Aurora\Exceptions\ConflictException;
use Aurora\Repositories\ExerciseRepository;

final class ExerciseCatalogService
{
    public function __construct(private ExerciseRepository $exercises, private Transaction $transaction) {}

    public function list(): array
    {
        return ['ok' => true, 'catalog' => $this->exercises->all()];
    }

    public function save(array $exercise): array
    {
        return $this->transaction->run(function () use ($exercise): array {
            if ($this->exercises->hasDuplicate($exercise)) {
                throw new ConflictException(['error' => 'Já existe um exercício com esse nome nesse grupo muscular']);
            }
            $current = $this->exercises->find($exercise['id']);
            if ($current !== null && $current['mode'] !== $exercise['mode'] && $this->exercises->references($exercise['id']) > 0) {
                throw new ConflictException(['error' => 'Este exercício já está em uma ficha. Remova-o dos planos antes de mudar entre força e cardio.']);
            }
            $this->exercises->save($exercise);
            return ['ok' => true, 'exercise' => $exercise];
        });
    }

    public function delete(string $id): array
    {
        return $this->transaction->run(function () use ($id): array {
            if ($this->exercises->references($id) > 0) {
                throw new ConflictException(['error' => 'Este exercício está em uma ou mais fichas. Retire-o dos planos antes de excluir.']);
            }
            $this->exercises->delete($id);
            return ['ok' => true];
        });
    }
}
