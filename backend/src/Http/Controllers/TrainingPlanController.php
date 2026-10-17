<?php
declare(strict_types=1);

namespace Aurora\Http\Controllers;

use Aurora\Exceptions\ValidationException;
use Aurora\Http\Requests\SaveTrainingPlanRequest;
use Aurora\Services\TrainingPlanService;

final class TrainingPlanController
{
    public function __construct(private TrainingPlanService $service) {}

    public function show(array $input): array
    {
        $person = $input['person'] ?? '';
        if (!is_string($person) || $person === '') {
            throw new ValidationException('Perfil não informado');
        }
        return $this->service->read($person);
    }

    public function save(array $input): array
    {
        return $this->service->save(SaveTrainingPlanRequest::validate($input));
    }
}
