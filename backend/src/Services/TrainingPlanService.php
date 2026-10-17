<?php
declare(strict_types=1);

namespace Aurora\Services;

use Aurora\Database\Transaction;
use Aurora\Exceptions\ConflictException;
use Aurora\Exceptions\ValidationException;
use Aurora\Repositories\ExerciseRepository;
use Aurora\Repositories\FitnessStateRepository;
use Aurora\Repositories\TrainingPlanRepository;

final class TrainingPlanService
{
    public function __construct(
        private TrainingPlanRepository $plans,
        private FitnessStateRepository $state,
        private ExerciseRepository $exercises,
        private Transaction $transaction,
    ) {}

    public function read(string $personId): array
    {
        return ['ok' => true, 'personExists' => $this->state->personExists($personId)] + $this->plans->read($personId);
    }

    public function save(array $input): array
    {
        return $this->transaction->run(function () use ($input): array {
            $personId = $input['personId'];
            if (!$this->state->personExists($personId)) {
                throw new ConflictException(['error' => 'Esse perfil ainda não está gravado no SQL. Abra o Fitness conectado e tente novamente.']);
            }
            $revision = $this->plans->revision($personId);
            if ($input['expectedRevision'] !== $revision) {
                throw new ConflictException(['conflict' => true, 'error' => 'O plano mudou em outro aparelho. Recarregue a página antes de salvar.']);
            }
            $plans = $this->resolveCatalog($input['plans']);
            $this->plans->replace($personId, $plans, $input['days']);
            $this->plans->saveRevision($personId, $revision + 1);
            return ['ok' => true, 'revision' => $revision + 1];
        });
    }

    private function resolveCatalog(array $plans): array
    {
        foreach ($plans as &$plan) {
            foreach ($plan['exercises'] as &$exercise) {
                $catalog = $this->exercises->find($exercise['catalogId']);
                if ($catalog === null || !(int)$catalog['active']) {
                    throw new ValidationException('O exercício selecionado não está mais no catálogo SQL');
                }
                if ($exercise['mode'] !== $catalog['mode']) {
                    throw new ValidationException('O tipo do exercício mudou no catálogo. Recarregue o plano e tente novamente.');
                }
                $exercise['muscleGroup'] = $catalog['muscle_group'];
                $exercise['name'] = $catalog['exercise_name'];
                $exercise['mode'] = $catalog['mode'];
            }
            unset($exercise);
        }
        unset($plan);
        return $plans;
    }
}
